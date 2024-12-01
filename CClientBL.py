from protocol import *
import os



class CClientBL:

    def __init__(self, host: str, port: int):

        self._client_socket = None
        self._host = host
        self._port = port

    def connect(self) -> socket:
        try:
            self._client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self._client_socket.connect((self._host,self._port))
            write_to_log(f"[CLIENT_BL] {self._client_socket.getsockname()} connected")
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
    client.send_wav("test.wav")
    client.send_wav("test.wav")
    client.disconnect()




