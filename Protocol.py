import socket

from MusicalAnalysis import AudioAnalyzer, MidiAnalyzer
from SecurityProtocol import *
from DBProtocol import *
import os
import ast
import uuid

def compare_melody(client_data, db_data):
    # will compare the entered melody to the melodies of some specific song in db
    pass


def best_matches(data):
    # will iterate through the database and compare the values, then will return the 10 closest matches
    pass


def parse_client_message(data):
    data = to_bytes(data)
    res = data.split(DELIMITER)
    if len(res) != 3:
        return None
    session, device, cmd_with_args = res
    if len(cmd_with_args.split(b">")) == 1:
        return session, device, cmd_with_args, None
    return session, device, cmd_with_args.split(b">")[0], cmd_with_args.split(b">")[1]


def check_cmd(cmd):
    if type(cmd) == bytes:
        cmd = cmd.decode(FORMAT)
    if cmd in REQUESTS_1:
        return 1
    if cmd in REQUESTS_2:
        return 2
    if cmd in LOGIN_REQUESTS:
        return 3
    return 0


def create_request_msg(public_key, data, session_id, device_id) -> str:
    """Create a valid protocol message and encrypt it using RSA, will be sent by client, with length field"""
    request = ''
    request += session_id + DELIMITER.decode(FORMAT) + device_id + DELIMITER.decode(FORMAT)
    if check_cmd(data.split(">")[0]) != 0:
        request += f"{data}"
    else:
        raise Exception("I had to witness an unbelievable blasphemy.")
    request = encrypt_msg(public_key, request)
    # return f"{len(str(request)):0{HEADER_LEN}d}".encode(FORMAT) + DELIMITER  + request
    return f"{len(request):0{HEADER_LEN}d}".encode(FORMAT) + request


def create_response_msg(public_key, data) -> str:
    """Encrypt and make the given protocol response valid, will be sent by server, with length field"""
    response = encrypt_msg(public_key, data)
    if response is None:
        response = b''
    # return f"{len(str(response)):0{HEADER_LEN}d}".encode(FORMAT) + response
    return f"{len(response):0{HEADER_LEN}d}".encode(FORMAT) + response


def create_response_and_execute_reaction(data, session_id, client_handler): # Session id is kept in the client handler on the server side and thus cannot be obtained from client's message
    """Create and a valid protocol message, will be sent by server, with length field"""

    def handle_request_with_file():
        file_name = None
        file_type = None
        if args["file"] != "":
            write_to_log("[SERVER_BL] receiving file...")
            # new file name is defined by how many files have been created
            is_recv, file_name = receive_file(client_handler.client_socket, args["file"])
            file_type = file_name.split(".")[-1]
            if not is_recv:
                write_to_log("Error - file count not be transferred")

        result = add_request(args, session_id, file_name, file_type)
        if args["file"] != "":
            os.remove(file_name)
        return result

    def handle_song_search():
        #try:
        write_to_log("[SERVER_BL] receiving file...")
        is_recv, file_name = receive_file(client_handler.client_socket, "wav")
        if not is_recv:
            write_to_log("Error - file count not be transferred")
            return
        songs = fetch_songs()
        # write_to_log(f"[PROTOCOL] fetched songs: {list(songs.keys())}")
        audio_analyzer = AudioAnalyzer(file_name)
        audio_analyzer.analyze_crepe(time_step=0.02, keep_stamps=True)
        write_to_log(7)
        midi_analyzer = MidiAnalyzer.load_from_audio_analyzer(audio_analyzer)
        write_to_log(8)
        res_best = midi_analyzer.compare_to_db(songs)
        write_to_log(9)
        os.remove(file_name)
        write_to_log(10)
        # write_to_log(f"[PROTOCOL] 20 best songs are: {res_best}")
        return f"{res_best}"
        # except Exception as e:
        #     write_to_log(f"Exception on handling song search: {e}")
        #     return "Error"

    msg = [item.decode(FORMAT) if type(item) == bytes else item for item in parse_client_message(data)]
    if msg is None:
        return "Invalid message"
    session, device, cmd, args = msg
    response = ""
    if args is not None:
        args = parse_args(args)
    if cmd in SESSION_REQUESTS:
        is_cmd_allowed = handle_session_limit(session)
        if not is_cmd_allowed:
            return "Invalid session"
    if check_cmd(data) == 1:
        response = REQUESTS_1[cmd]
    elif cmd == "Register":
        response = register_client(args)
    elif cmd == "Login_with_data":
        response, session_code, client_handler.session = login_with_data(args)
        response += ">" + session_code
    elif cmd == "Login_with_session":
        response, client_handler.session = login_with_old_session(session)
    elif cmd == "Request":
        response = handle_request_with_file()
    elif cmd == "Delete_session":
        response = delete_session(session_id)
    elif cmd == "Songs":
        song_names = fetch_song_names(args)
        response = str(song_names)
    elif cmd == SEARCH_SONG_REQUEST:
        response = handle_song_search()
    else:
        response = "Error"
    if response == "Bye!":
        client_handler.connected = False
        toggle_session_state(session_id, False)
    return response


def get_complete_file_path(file_type, file_name, dir):
    project_folder = os.getcwd()  # Get the project folder path
    os.makedirs(dir, exist_ok=True)  # Ensure the directory exists
    unique_id = uuid.uuid4().hex  # Generate a unique identifier
    file_path = os.path.join(project_folder, dir, f"{file_name}_{unique_id}.{file_type}")
    return file_path


def receive_file(client_socket, file_type):
    initial_timeout = client_socket.timeout
    try:
        client_socket.settimeout(None) # Set a bigger timeout to avoid transmission issues
        file_name = get_complete_file_path(file_type, "file", "ServerFiles")
        # Read the file size as a string until the newline character
        file_size_bytes = b""
        while not file_size_bytes.endswith(b"\n"):
            chunk = client_socket.recv(1)
            if not chunk:
                write_to_log("[PROTOCOL] file transfer - failed to read file size from the client.")
                return False, ""
            file_size_bytes += chunk
        # Convert the file size from string to integer
        file_size = int(file_size_bytes.decode(FORMAT).strip())
        if file_size == 0:
            write_to_log("[PROTOCOL] file transfer - file size is 0, file not saved")
            return True, file_name
        bytes_received = 0
        with open(file_name, 'wb') as f:
            while bytes_received < file_size:
                # Calculate remaining bytes to read
                remaining_bytes = file_size - bytes_received
                # If there are less remaining bytes than the general buffer size, choose a corresponding buffer size
                bytes_to_read = min(BUFFER_SIZE, remaining_bytes)

                # Read the next chunk
                bytes_read = client_socket.recv(bytes_to_read)
                if not bytes_read:
                    # Unexpected disconnection
                    write_to_log("[PROTOCOL] file transfer - connection lost before file transfer was complete.")
                    return False, ""

                # Write to file and update received byte count
                f.write(bytes_read)
                bytes_received += len(bytes_read)
        client_socket.settimeout(initial_timeout)
        return True, file_name
    except Exception as e:
        client_socket.settimeout(initial_timeout)
        write_to_log(f"[PROTOCOL] exception file transfer - {e}")
        return False, ""


def receive_msg(my_socket: socket, private_key) -> (bool, str):
    """Decrypt and extract message from protocol, without the length field
       If length field does not include a number, returns False, "Error" """
    try:
        str_header = my_socket.recv(HEADER_LEN).decode(FORMAT)
        length = int(str_header)
        if length > 0:
            buf_encrypted = my_socket.recv(length)
            buf = decrypt_msg(private_key, buf_encrypted)
        else:
            return False, "Error"

        return True, buf

    except socket.timeout:
        return False, "Socket Timeout"

    except (socket.error, ConnectionResetError):
        return False, "Server workflow terminated"

    except Exception as e:
        # write_to_log("[PROTOCOL] receive msg failed with exception {}".format(e))
        return False, e


def receive_key(my_socket:socket):
    str_header = my_socket.recv(HEADER_LEN).decode(FORMAT)
    length = int(str_header)
    if length > 0:
        pem = my_socket.recv(length).decode(FORMAT).encode(FORMAT)
        key = load_pem_public_key(pem)
        return key


def parse_args(data: str):
    try:
        # Convert the string representation of a dictionary back to a Python dictionary
        dictionary = ast.literal_eval(data)
        return dictionary
    except Exception as e:
        write_to_log(f"Exception on parsing arguments {e} on data {data}")


REQUESTS_1 = {"Hello": "Hello!", "Find": best_matches,
              SEND_FILE_SUCCESS: SEND_FILE_SUCCESS, SEND_FILE_FAIL: SEND_FILE_FAIL, DISCONNECT_MSG: "Bye!", "Update": "All Good", "Songs": "K"}

REQUESTS_2 = {"Register", "Request", "Delete_session", SEARCH_SONG_REQUEST}


LOGIN_REQUESTS = {"Login_with_session", "Login_with_data"}

SESSION_REQUESTS = {"Request", "Login_with_session", "Delete_session", SEARCH_SONG_REQUEST, "Upd"}
