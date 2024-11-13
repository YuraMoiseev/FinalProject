from protocol import *


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


