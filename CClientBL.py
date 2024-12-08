from protocol import *
import os
import pyaudio
import wave
from threading import Event

class CClientBL:

    def __init__(self, host: str, port: int):

        self._client_socket = None
        self._host = host
        self._port = port

        self.RECORD = False
        self.stop_event = None
    def connect(self) -> socket:
        try:
            self._client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self._client_socket.connect((self._host,self._port))
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} connected")
            self.stop_event = Event()
            return self._client_socket
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on connect: {}".format(e))
            return None

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
            msg = create_request_msg(msg)
            message = msg.encode(FORMAT)
            self._client_socket.send(message)
            write_to_log(f"[CLIENT_BL] send {self._client_socket.getsockname()} {msg} ")
            return True
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on send_data: {}".format(e))
            return False

    def send_wav(self, file_name: str) -> bool:
        if not os.path.exists(file_name):
            write_to_log(f"[CLIENT_BL] - file does not exist: {file_name}")
            return False
        self.send_data(SEND_FILE_REQUEST)
        try:
            if self.receive_data() == SEND_FILE_APPROVE:
                # Get the size of the file
                file_size = os.path.getsize(file_name)

                # Send the file size as a string followed by a newline
                self._client_socket.send(f"{file_size}\n".encode())

                # Send the file data
                with open(file_name, 'rb') as f:
                    while True:
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            # File transmission is done
                            break
                        self._client_socket.send(bytes_read)

                # Log the file transfer
                write_to_log(f"[CLIENT_BL] sent {self._client_socket.getsockname()} wav file {file_name}")
                write_to_log(f"[CLIENT_BL] received from [SERVER_BL] {self.receive_data()}")
                return True
            else:
                raise Exception(f"[CLIENT_BL] - sending {file_name} was not approved")
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on send_wav: {}".format(e))
            self._client_socket.send(f"{0}\n".encode())
            self._client_socket.send(b"0")
            write_to_log(f"[CLIENT_BL] received from [SERVER_BL] {self.receive_data()}")
            return False

    def record_wav(self, file_name: str) -> bool:
        try:
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} recording {file_name}...")
            chunk = 1024  # Record in chunks of 1024 samples
            sample_format = pyaudio.paInt16  # 16 bits per sample
            channels = 1
            fs = 44100  # Record at 44100 samples per second
            seconds = 10
            p = pyaudio.PyAudio()  # Create an interface to PortAudio

            write_to_log('[CLIENT_BL] Recording wav file')

            stream = p.open(format=sample_format,
                            channels=channels,
                            rate=fs,
                            frames_per_buffer=chunk,
                            input=True)

            frames = []  # Initialize array to store frames
            # Store data in chunks for the given time
            for i in range(0, int(fs / chunk * seconds)):
                data = stream.read(chunk)
                frames.append(data)
                if self.stop_event.is_set():
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
            (bres, msg) = receive_msg(self._client_socket)
            if bres:
                write_to_log(f"[CLIENT_BL] received {self._client_socket.getsockname()} {msg} ")
                return msg
            else:
                write_to_log("[CLIENT_BL] Invalid msg")
                return "Invalid msg"
        except Exception as e:
            write_to_log("[CLIENT_BL] Exception on receive: {}".format(e))
            return ""


if __name__ == "__main__":
    client = CClientBL(CLIENT_HOST, PORT)
    client.connect()
    client.send_data("Hello")
    write_to_log(client.receive_data())
    # client.send_wav("test.wav")
    # client.send_wav("test.wav")
    # client.send_wav("test1.wav")
    # client.send_wav("test.wav")
    client.record_wav("recording.wav")
    client.send_wav("recording.wav")
    client.receive_data()
    client.disconnect()
