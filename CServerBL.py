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

            # self._server_socket.setblocking(False)
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
                    if not self._is_srv_running:
                        write_to_log("1")
                    # Done for constant refreshing of socket accepting in case of a server workflow termination
                    continue

                # except BlockingIOError:
                #     if not self._is_srv_running:
                #         write_to_log("2")
                #     # Done for constant refreshing of socket accepting in case of a server workflow termination
                #     continue

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
                    client_thread.close_socket()
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
        # self.client_socket.send(key)
        self.client_socket.send(f"{len(str(key)):0{HEADER_LEN}d}{key.decode()}".encode(FORMAT))

    def close_socket(self):
        self.connected = False
        self.client_socket.send(
            create_response_msg(self.client_public_key, create_response(DISCONNECT_MSG))
        )

    def receive_file(self, file_name):
        try:
            global count_file
            # Read the file size as a string until the newline character
            file_size_bytes = b""
            while not file_size_bytes.endswith(b"\n"):
                chunk = self.client_socket.recv(1)
                if not chunk:
                    raise Exception("Failed to read file size from the client.")
                file_size_bytes += chunk

            # Convert the file size from string to integer
            file_size = int(file_size_bytes.decode(FORMAT).strip())
            if file_size == 0:
                write_to_log("[SERVER_BL] File size is 0, file not saved")
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
                        raise Exception("Connection lost before file transfer was complete.")

                    # Write to file and update received byte count
                    f.write(bytes_read)
                    bytes_received += len(bytes_read)
            # One more wav file added
            count_file += 1
            return True
        except Exception as e:
            write_to_log("[CClientHandler] Exception in receive_wav: {}".format(e))
            raise e


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
                write_to_log(f"[SERVER_BL] received from {self.address} - {msg}")
                # 3. If valid command - create response
                # 4. Create response
                response = create_response(msg, self.session)
                # If registration is requested, invoke fire event on REGISTER_REQUEST
                if response == REG_MSG:
                    self.callback(REGISTER_REQUEST, self.address, msg[4:])
                    write_to_log("[SERVER_BL] REGISTER_REQUEST invoked")
                # 5. Handle a login request and if successful, save sessions id
                if self.session is None and check_cmd(msg) == 3:
                    if response[0] == LOGIN_SUCCESS:
                        self.session = response[1]
                    response = response[0]
                # 6. Handle log out
                if response == "Success":
                    self.session = None
                # 7. Save to log
                write_to_log(f"[SERVER_BL] send - {response}")
                # 8. Send response to the client
                self.client_socket.send(create_response_msg(self.client_public_key, response))
                # 9. If client sent file transfer request - invoke file receive event
                if response == SEND_FILE_APPROVE:
                    write_to_log("[SERVER_BL] receiving wav...")
                    # new file name is defined by how many files we have created
                    is_recv = self.receive_file(f"file{count_file + 1}")
                    if is_recv:
                        self.client_socket.send(
                            create_response_msg(self.client_public_key, create_response(SEND_FILE_SUCCESS)))
                        write_to_log(f"[SERVER_BL] {SEND_FILE_SUCCESS}")
                    else:
                        self.client_socket.send(
                            create_response_msg(self.client_public_key, create_response(SEND_FILE_FAIL)))

                        write_to_log(f"[SERVER_BL] {SEND_FILE_FAIL}")

                # Handle DISCONNECT command
                if msg.decode() == DISCONNECT_MSG:
                    self.connected = False
            if msg == "Socket Timeout":
                if not self.connected:
                    # Done for constant refreshing of socket accepting in case of a server workflow termination
                    continue
            # 9. Update the last action of the session
            if self.session is not None:
                update_last_action(self.session)

        # close the client socket and invoke fire event NEW_COMMAND to delete the client from the clients' table
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        write_to_log(f"[SERVER_BL] Thread closed for : {self.address} ")
        self.callback(CLOSE_CONNECTION, self.address, "")


if __name__ == "__main__":
    server = CServerBL(SERVER_HOST, PORT)
    server.start_server()

