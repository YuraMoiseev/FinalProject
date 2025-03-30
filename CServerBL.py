import threading
from Protocol import *

# events
NEW_CONNECTION: int = 1
REGISTER_APPROVE: int = 2
REGISTER_REQUEST: int = 3
CLOSE_CONNECTION: int = 4
count_file = 0


class CServerBL:

    def __init__(self, host, port):

        # Open the log file in write mode, which truncates the file to zero length
        with open(LOG_FILE, 'w'):
            pass  # This block is empty intentionally

        self._host = host
        self._port = port
        self._server_socket = None
        self._is_srv_running = True
        self._client_handlers = []

    def fire_event(self, enum_even: int, client_handle, args: str):
        pass

    def stop_server(self):
        try:
            self._is_srv_running = False

        except Exception as e:
            write_to_log("[SERVER_BL] Exception in Stop_Server fn : {}".format(e))

    def start_server(self):
        try:
            create_db_tables()
            # initialise the server socket and listen
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.bind((self._host, self._port))

            self._server_socket.settimeout(0.001)

            self._server_socket.listen(5)
            write_to_log(f"[SERVER_BL] listening...")
            while self._is_srv_running and self._server_socket is not None:

                try:
                    # Accept socket request for connection
                    client_socket, address = self._server_socket.accept()
                    write_to_log(f"[SERVER_BL] Client connected {client_socket}{address} ")

                    # Start Thread
                    cl_handler = CClientHandler(client_socket, address, self.fire_event)
                    cl_handler.start()
                    self._client_handlers.append(cl_handler)
                    write_to_log(f"[SERVER_BL] fire event - NEW_CONNECTION")
                    write_to_log(f"[SERVER_BL] ACTIVE CONNECTION {threading.active_count() - 1}")

                    # Invoke event NEW_CONNECTION
                    self.fire_event(NEW_CONNECTION, cl_handler.address, "")
                    write_to_log(f"[SERVER_BL] fire event - REGISTER_REQUEST")

                except socket.timeout:
                    # Done for constant refreshing of socket accepting in case of a server workflow termination
                    continue

                except Exception as e:
                    write_to_log(f"[SERVER_BL] - exception {e} on running")
        finally:

            # Close server socket
            if self._server_socket is not None:
                self._server_socket.close()
                self._server_socket = None

            if len(self._client_handlers) > 0:
                # Waiting to close all opened threads
                for client_thread in self._client_handlers:
                    try:
                        client_thread.close_socket()
                    except OSError: # catch already closed sockets
                        continue
                    client_thread.join()
                write_to_log(f"[SERVER_BL] All Client threads are closed")
            write_to_log(f"[SERVER_BL] Server thread is DONE")



def fire_event(enum_even: int, client_handle, args: str):
    pass  # This block is empty intentionally


class CClientHandler(threading.Thread):

    def __init__(self, client_socket, address, fn):
        super().__init__()

        self.client_socket = client_socket
        self.address = address
        self.callback = fn
        self.client_public_key = None
        self._private_key = create_private_key()
        self.connected = False
        self.session = None

    def exchange_keys(self):
        key = load_pem(self._private_key.public_key())
        self.client_public_key = receive_key(self.client_socket)
        self.client_socket.send(f"{len(str(key)):0{HEADER_LEN}d}{key.decode()}".encode(FORMAT))

    def close_socket(self):
        self.connected = False
        if self.client_socket is not None:
            self.client_socket.send(
                create_response_msg(self.client_public_key, create_response_and_execute_reaction(DISCONNECT_MSG, self.session, self))
            )


    # TODO: move to protocol with socket as an argument
    def receive_file(self, file_type):
        try:
            file_name = get_complete_file_path(file_type, "file", "ServerFiles")
            # Read the file size as a string until the newline character
            file_size_bytes = b""
            while not file_size_bytes.endswith(b"\n"):
                chunk = self.client_socket.recv(1)
                if not chunk:
                    write_to_log("[SERVER_BL] file transfer - failed to read file size from the client.")
                    return False
                file_size_bytes += chunk

            # Convert the file size from string to integer
            file_size = int(file_size_bytes.decode(FORMAT).strip())
            if file_size == 0:
                write_to_log("[SERVER_BL] file transfer - file size is 0, file not saved")
                return True

            bytes_received = 0
            with open(file_name, 'wb') as f:
                while bytes_received < file_size:
                    # Calculate remaining bytes to read
                    remaining_bytes = file_size - bytes_received
                    # If there are less remaining bytes than the general buffer size, choose a corresponding buffer size
                    bytes_to_read = min(BUFFER_SIZE, remaining_bytes)

                    # Read the next chunk
                    bytes_read = self.client_socket.recv(bytes_to_read)
                    if not bytes_read:
                        # Unexpected disconnection
                        write_to_log("[SERVER_BL] file transfer - connection lost before file transfer was complete.")
                        return False

                    # Write to file and update received byte count
                    f.write(bytes_read)
                    bytes_received += len(bytes_read)
            return True
        except Exception as e:
            write_to_log(f"[SERVER_BL] exception file transfer - {e}")
            return False


    def run(self):
        # This code run in separate thread for every client
        self.exchange_keys()
        self.connected = True
        self.client_socket.settimeout(0.001)
        while self.connected:
            # 1. Get message from socket and check it
            valid_msg, msg = receive_msg(self.client_socket, self._private_key)
            if valid_msg:
                # 2. Save to log
                if msg != b'Update':
                    # write_to_log(f"[SERVER_BL] received from {self.address} - {msg}")
                    pass
                # 3. If valid command - create response
                # 4. Create response
                response = create_response_and_execute_reaction(msg, self.session, self)
                # 5. If registration is requested, invoke fire event on REGISTER_REQUEST
                if response == REG_MSG:
                    self.callback(REGISTER_REQUEST, self.address, msg[4:])
                    write_to_log("[SERVER_BL] REGISTER_REQUEST invoked")
                # 6. Save to log
                if response != "All Good":
                    write_to_log(f"[SERVER_BL] send - {response}")
                # 7. Send response to the client
                self.client_socket.send(create_response_msg(self.client_public_key, response))
            if msg == "Socket Timeout":
                if not self.connected:
                    # Done for constant refreshing of socket accepting in case of a server workflow termination
                    continue
            # 8. Check when was the last action of the session, handle respectively

        # close the client socket and invoke fire event NEW_COMMAND to delete the client from the clients' table
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        write_to_log(f"[SERVER_BL] Thread closed for : {self.address} ")
        self.callback(CLOSE_CONNECTION, self.address, "")


if __name__ == "__main__":
    server = CServerBL(SERVER_HOST, PORT)
    server.start_server()

