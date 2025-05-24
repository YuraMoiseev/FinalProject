# Libraries
import pyaudio
import wave
import subprocess
import hashlib

# Local
from CLIENT.Protocols.Protocol import *
from CLIENT.Protocols.PacketProtocol import *
from CLIENT.config_utils.config import HEADER_LEN, DISCONNECT_MSG, KEY_ROTATION_COUNTDOWN, CLIENT_HOST, PORT, SEARCH_SONG_REQUEST, FORMAT

class CClientBL:

    def __init__(self, host: str, port: int):

        self._client_socket = None
        self._host = host
        self._port = port

        self._private_key = create_private_key()
        self.packet_handler = PacketHandler(Agent.Client, self._private_key, None)
        self.session_token = SessionToken()
        self.serv_public_key = None
        self.is_recording = False
        self._audio_devices = None
        self.check_existing_session()
        self.get_device_id()
        self.selected_audio_device = 0
        self.pending_requests = set()
        self.key_rotation_countdown = 0

    def check_existing_session(self, file_path="session.txt"):
        """Check if the file exists and is non-empty. If not, write content to it."""
        try:
            # Check if the file exists and is non-empty
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                with open(file_path, "r") as f:
                    self.session_token.session_code = f.read()

            else:
                self.session_token.session_code = ''
            return str(self.session_token.session_code)

        except Exception as e:
            print(f"[CLIENT_BL] Exception in checking existing session: {e}")
            self.session_token.session_code = ''
            return str(self.session_token.session_code)

    def refresh_session_file(self, session, file_path="session.txt"):
        with open(file_path, "w") as f:
            f.write(session)
        self.check_existing_session(file_path)

    def get_device_id(self):
        # Get various system identifiers
        identifiers = []

        # BIOS serial
        try:
            result = subprocess.check_output('wmic bios get serialnumber', shell=True)
            bios_serial = result.decode().split('\n')[1].strip()
            if bios_serial:
                identifiers.append(bios_serial)
        except Exception as e:
            write_to_log(f"Exception in creating device id - {e}")
            raise e

        hash_object = hashlib.sha256(''.join(identifiers).encode())
        self.device_id = hash_object.hexdigest()
        return self.device_id

    def connect(self) -> socket:
        try:
            self._client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self._client_socket.connect((self._host,self._port))
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} connected")
            # self._client_socket.send(self._private_key.public_key())
            self.exchange_rsa_keys()
            return self._client_socket
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on connect: {}".format(e))
            return None

    def exchange_rsa_keys(self):
        key = load_pem(self._private_key.public_key())
        key_string = f"{len(str(key)):0{HEADER_LEN}d}{key.decode(FORMAT)}".encode(FORMAT)
        self._client_socket.send(key_string)
        self.serv_public_key = receive_key(self._client_socket)

    def disconnect(self) -> bool:
        try:
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} closing")
            self.send_data(DISCONNECT_MSG, {})
            self._client_socket.close()
            return True
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on disconnect: {}".format(e))
            return False
        
    def rotate_symmetric_keys(self):
        try: 
            # Send a request to server to rotate the symmetric key. The key change is handled automatically by the packet handler
            key_message_packet = Packet.create(packet_type=Agent.Client | MsgType.Regular, session_token=self.session_token, msg="Rotate_key")
            key_message = pack_message(key_message_packet, self.packet_handler, EncryptionKey.RSA | DumpType.Short, self.serv_public_key)
            self._client_socket.send(key_message)
            self.receive_data(True)
            self.key_rotation_countdown = KEY_ROTATION_COUNTDOWN
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on rotating keys: {}".format(e))
            return False

    def send_data(self, msg: str, args: dict) -> bool:
        try:
            # Rotate keys if needed
            if self.key_rotation_countdown == 0:
                self.rotate_symmetric_keys()
            # Create a packet and dump it into a string
            message_packet = Packet.create(session_token=self.session_token, msg=msg, args=args)
            self.pending_requests.add(message_packet.header["packet_id"])
            message = pack_message(message_packet, self.packet_handler, EncryptionKey.Fernet | DumpType.Regular, self.serv_public_key)
            write_to_log(f"Client is about to send {message.decode()}")
            self._client_socket.send(message)
            self.key_rotation_countdown -= 1
            return True
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on send_data: {}".format(e))
            write_to_log(msg)
            return False
        
    def receive_data(self, ignore_id=False) -> Packet:
        try:
            (bres, packet, parse_msg) = receive_msg(self._client_socket, self.packet_handler)
            print(packet)
            if bres:
                write_to_log(f"[CLIENT_BL] received {self._client_socket.getsockname()} {packet.body['msg']} with parse message {parse_msg}")
                if not ignore_id:
                    self.delete_request(packet.body["id"])
                return packet
            else:
                if not ignore_id:
                    self.delete_request(packet.body["id"])
                write_to_log(f"[CLIENT_BL] error on receiving data - {packet.body['msg']} with parse message {parse_msg}")
                return packet
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on receive: {}".format(e))
            return Packet.create(msg="Exception")

    def cond(self):
        self.is_recording = not self.is_recording

    @staticmethod
    def get_audio_devices():
        p = pyaudio.PyAudio()
        devices = {}
        # List all available audio devices
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices[info['name']] = i
        p.terminate()
        return devices

    def select_audio_device(self, name: str):
        try:
            self.selected_audio_device = self.get_audio_devices()[name]
            write_to_log(f"[CLIENT_BL] successfully changed audio device to {self.selected_audio_device} ({name})")
        except Exception as e:
            write_to_log(f"Exception on selection audio device - {e}")
        
    def delete_request(self, packet_id: str):
        try: 
            if packet_id not in self.pending_requests:
                raise Exception("Error on removing request - unknown request id")
            self.pending_requests.remove(packet_id)
        except Exception as e:
            write_to_log(f"Error on removing request - {e}")


    def record_wav(self, file_name: str = "recording.wav") -> bool:
        try:
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} recording {file_name}...")
            chunk = 1024  # Record in chunks of 1024 samples
            sample_format = pyaudio.paInt32  # 32 bits per sample
            channels = 1
            fs = 44100  # Record at 44100 samples per second
            seconds = 3  # Record for 3 seconds
            p = pyaudio.PyAudio()  # Create an interface to PortAudio

            write_to_log('[CLIENT_BL] Recording wav file')

            stream = p.open(format=sample_format,
                            channels=channels,
                            rate=fs,
                            frames_per_buffer=chunk,
                            input_device_index=self.selected_audio_device,
                            input=True)

            frames = []  # Initialize array to store frames
            # Store data in chunks for the given time
            for i in range(0, int(fs / chunk * seconds)):
                data = stream.read(chunk)
                frames.append(data)
                if not self.is_recording:
                    write_to_log("[CLIENT_BL] recording stopped unexpectedly")
                    return False
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            # Terminate the PortAudio interface
            p.terminate()

            write_to_log('[CLIENT_BL] finished recording')

            # Save the recorded data as a WAV file
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            wf = wave.open(file_name, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(frames))
            wf.close()
            return True

        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on record_wav: {}".format(e))
            return False


import time
if __name__ == "__main__":
    # file_path = "C:/Users\Ymois\PycharmProjects\FinalProject\MusicFiles\Audio\TestAdele.wav"
    file_path = "/MusicFiles/Audio/RitD.wav"
    client = CClientBL(CLIENT_HOST, PORT)
    client.connect()
    # write_to_log(client.receive_data())
    # client.send_wav("test.wav")
    # client.send_wav("test.wav")
    # client.send_wav("test1.wav")
    # client.send_wav("test.wav")
    # client.record_wav("recording.wav")
    # client.send_wav("recording.wav")
    # client.record_wav()
    time.sleep(5)
    client.send_data(f"Login_with_session", {})
    a = client.receive_data()
    write_to_log(str(a))
    client.send_data(SEARCH_SONG_REQUEST, {})
    a = client.receive_data()
    write_to_log(str(a))
    filename = "/MusicFiles/Audio/RitD.wav"
    send_file(filename, client._client_socket, client.packet_handler)
    a = client.receive_data()
    write_to_log(str(a))
    client.disconnect()


