import socket
from SecurityProtocol import *
from DBProtocol import *

def compare_melody(client_data, db_data):
    # will compare the entered melody to the melodies of some specific song in db
    pass


def best_matches(data):
    # will iterate through the database and compare the values, then will return the 10 closest matches
    pass


def parse_message(data):
    data = to_bytes(data)
    data = data.decode(FORMAT)
    if ">" in data:
        return data[:data.index(">")], data[data.index(">")+1:]
    return data, None


def check_cmd(data):
    cmd, args = parse_message(data)
    if type(cmd) == bytes:
        cmd = cmd.decode(FORMAT)
    if cmd in REQUESTS_1:
        return 1
    if cmd in REQUESTS_2:
        return 2
    if cmd in LOGIN_REQUESTS:
        return 3
    return 0


def create_request_msg(public_key, data) -> str:
    """Create a valid protocol message and encrypt it using RSA, will be sent by client, with length field"""
    request = ''
    if check_cmd(data) != 0:
        request += f"{data}"
    else:
        request = f"Non-supported cmd"
    request = encrypt_msg(public_key, request)
    return f"{len(str(request)):0{HEADER_LEN}d}".encode(FORMAT) + DELIMITER  + request


def create_response_msg(public_key, data) -> str:
    """Encrypt and make the given protocol response valid, will be sent by server, with length field"""
    response = encrypt_msg(public_key, data)
    if response is None:
        response = b''
    return f"{len(str(response)):0{HEADER_LEN}d}".encode(FORMAT) + response


def create_response(data, session_id=None): # Session id is kept in the client handler on the server side and thus cannot be obtained from client's message
    """Create and a valid protocol message, will be sent by server, with length field"""
    cmd, args = parse_message(data)
    if type(cmd) == bytes:
        cmd = cmd.decode(FORMAT)
    if type(args) == bytes:
        args = args.decode(FORMAT)
    if check_cmd(data) == 1:
        response = REQUESTS_1[cmd]
    elif cmd == "Register":
        response = register_client(args)
    elif cmd == "Login_with_data":
        response = login_with_data(args)
    elif cmd == "Request":
        response = add_request(args, session_id)
    elif cmd == "Login_with_session":
        response = login_with_old_session(args)
    elif cmd == "Delete_session":
        response = delete_session(session_id)
    else:
        response = "Non-supported cmd"
    return response



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


REQUESTS_1 = {"Hello": "Hello!", "Find": best_matches, SEND_FILE_REQUEST: SEND_FILE_APPROVE,
              SEND_FILE_SUCCESS: SEND_FILE_SUCCESS, SEND_FILE_FAIL: SEND_FILE_FAIL, DISCONNECT_MSG: "Bye!"}

REQUESTS_2 = ["Register", "Request", "Delete_session"]


LOGIN_REQUESTS = ["Login_with_session", "Login_with_data"]

