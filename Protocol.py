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
    return cmd in REQUESTS


def create_request_msg(public_key, data) -> str:
    """Create a valid protocol message and encrypt it using RSA, will be sent by client, with length field"""
    request = ''
    if check_cmd(data):
        request += f"{data}"
    else:
        request = f"Non-supported cmd"
    request = encrypt_msg(public_key, request)
    return f"{len(str(request)):0{HEADER_LEN}d}".encode(FORMAT) + DELIMITER  + request


def create_response_msg(public_key, data) -> str:
    """Encrypt and make the given protocol response valid, will be sent by server, with length field"""
    response = encrypt_msg(public_key, data)
    return f"{len(str(response)):0{HEADER_LEN}d}".encode(FORMAT) + DELIMITER  + response


def create_response(data):
    """Create and a valid protocol message, will be sent by server, with length field"""
    cmd, args = parse_message(data)
    if type(cmd) == bytes:
        cmd = cmd.decode(FORMAT)
    if type(args) == bytes:
        args = args.decode(FORMAT)
    if check_cmd(data) and cmd !="Register" and cmd !="Login":
        response = REQUESTS[cmd]
    elif cmd == "Register":
        response = register_client(args)
    elif cmd == "Login":
        response = check_password(args)
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
    except Exception as e:
        write_to_log("[PROTOCOL] receive msg failed with exception {}".format(e))


def receive_key(my_socket:socket):
    str_header = my_socket.recv(HEADER_LEN).decode(FORMAT)
    length = int(str_header)
    if length > 0:
        pem = my_socket.recv(length).decode(FORMAT).encode(FORMAT)
        key = load_pem_public_key(pem)
        return key

# def receive_key(my_socket:socket):
#     pem = my_socket.recv(BUFFER_SIZE)
#     write_to_log(pem)
#     key = load_pem_public_key(pem)
#     return key


REQUESTS = {"Hello": "Hello!", "Find": best_matches, SEND_FILE_REQUEST: SEND_FILE_APPROVE,
                SEND_FILE_SUCCESS: SEND_FILE_SUCCESS, SEND_FILE_FAIL: SEND_FILE_FAIL, DISCONNECT_MSG: "Bye!",
                "Register": "", "Login": "", "Question": "Answer", "How do I become a coder?": "ChatGPT(no)"}

