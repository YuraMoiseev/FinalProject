import time

from Protocol import *
import os
import pyaudio
import wave
import uuid

class CClientBL:

    def __init__(self, host: str, port: int):

        self._client_socket = None
        self._host = host
        self._port = port

        self._private_key = create_private_key()
        self.serv_public_key = None
        self.is_recording = False
        self._audio_devices = None
        self.device_id = str(uuid.getnode()) # MAC address-based ID
        self.selected_audio_device = 0

    def connect(self) -> socket:
        try:
            self._client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self._client_socket.connect((self._host,self._port))
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} connected")
            # self._client_socket.send(self._private_key.public_key())
            self.exchange_keys()
            return self._client_socket
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on connect: {}".format(e))
            return None

    def exchange_keys(self):
        key = load_pem(self._private_key.public_key())
        self._client_socket.send(f"{len(str(key)):0{HEADER_LEN}d}{key.decode(FORMAT)}".encode(FORMAT))
        self.serv_public_key = receive_key(self._client_socket)

    def disconnect(self) -> bool:
        try:
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} closing")
            self.send_data(DISCONNECT_MSG)
            self._client_socket.close()
            return True
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on disconnect: {}".format(e))
            return False

    def send_data(self, msg: str) -> bool:
        try:
            msg = create_request_msg(self.serv_public_key, msg)
            message = msg#.encode(FORMAT)
            self._client_socket.send(message)
            write_to_log(f"[CLIENT_BL] send {self._client_socket.getsockname()} {msg} ")
            return True
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on send_data: {}".format(e))
            write_to_log(msg)
            return False

    def cond(self):
        self.is_recording = not self.is_recording
        write_to_log(self.is_recording)

    def get_audio_devices(self):
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

    def send_file(self, file_name: str) -> bool:
        if not os.path.exists(file_name):
            write_to_log(f"[CLIENT_BL] - file does not exist: {file_name}")
            return False
        self.send_data(SEND_FILE_REQUEST)
        try:
            if self.receive_data() == SEND_FILE_APPROVE:
                # Get the size of the file
                file_size = os.path.getsize(file_name)

                # Send the file size as a string followed by a newline
                self._client_socket.send(f"{file_size}\n".encode(FORMAT))

                # Send the file data
                with open(file_name, 'rb') as f:
                    while True:
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            # File transmission is done
                            break
                        # self._client_socket.send(encrypt_msg(self.serv_public_key, bytes_read))
                        self._client_socket.send(bytes_read)

                # Log the file transfer
                write_to_log(f"[CLIENT_BL] sent {self._client_socket.getsockname()} wav file {file_name}")
                write_to_log(f"[CLIENT_BL] received from [SERVER_BL] {self.receive_data()}")
                return True
            else:
                write_to_log("[CLIENT_BL] - sending {file_name} was not approved")
                return False

        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on send_wav: {}".format(e))
            self._client_socket.send(f"{0}\n".encode())
            self._client_socket.send(b"0")
            write_to_log(f"[CLIENT_BL] received from [SERVER_BL] {self.receive_data()}")
            return False

    def record_wav(self, file_name: str = "recording.wav") -> bool:
        try:
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} recording {file_name}...")
            chunk = 1024  # Record in chunks of 1024 samples
            sample_format = pyaudio.paInt32  # 32 bits per sample
            channels = 1
            fs = 44100  # Record at 44100 samples per second
            seconds = 10  # Record for 3 seconds
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

    def receive_data(self) -> str:
        try:
            (bres, msg) = receive_msg(self._client_socket, self._private_key)
            if bres:
                write_to_log(f"[CLIENT_BL] received {self._client_socket.getsockname()} {msg.decode(FORMAT)} ")
                return msg.decode(FORMAT)
            else:
                write_to_log(f"[CLIENT_BL] error - {msg}")
                return msg
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on receive: {}".format(e))
            return ""



if __name__ == "__main__":
    client = CClientBL(CLIENT_HOST, PORT)
    client.connect()
    # write_to_log(client.receive_data())
    # client.send_wav("test.wav")
    # client.send_wav("test.wav")
    # client.send_wav("test1.wav")
    # client.send_wav("test.wav")
    # client.record_wav("recording.wav")
    # client.send_wav("recording.wav")
    client.record_wav()
    client.send_file("recording.wav")
    client.receive_data()
    client.disconnect()
