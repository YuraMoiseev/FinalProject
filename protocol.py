import socket
import sqlite3
from SecurityProtocol import *
from ConstantsAndLogging import *

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


def create_users_table():
    # create users table in DB
    connection = sqlite3.connect("Users.db")
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    login TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL
    );
    ''')
    connection.commit()
    connection.close()

def register_client(data):
    try:
        username, email, password = parse_args(str(data))
        hashed_password = hash_password(password)
        connection = sqlite3.connect("Users.db")
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM Users WHERE login = ? OR email = ?", (username, email))
        if cursor.fetchone() is not None:
            connection.commit()
            connection.close()
            return REG_FAIL_USERNAME
        cursor.execute(
            'INSERT INTO Users (login, email, hashed_password) VALUES (?, ?, ?)',
            (username, email, hashed_password)
        )
        connection.commit()
        connection.close()
        return REG_SUCCESS
    except Exception as e:
        write_to_log("[PROTOCOL] - exception on registering a client - {}".format(e))


def check_password(data):
    try:
        username_or_email, none, password = parse_args(str(data))
        connection = sqlite3.connect("Users.db")
        cursor = connection.cursor()
        cursor.execute("SELECT hashed_password FROM Users WHERE login = ? OR email = ?", (username_or_email, username_or_email))
        result = cursor.fetchone()
        if result is None:
            return LOGIN_FAIL + " - no such user was found in database"
        hashed_password = result[0]
        connection.commit()
        connection.close()
        if verify_password(hashed_password, password):
            return LOGIN_SUCCESS
        else:
            return LOGIN_FAIL + " - incorrect password"
    except Exception as e:
        write_to_log("[PROTOCOL] - exception on checking password - {}".format(e))


def parse_args(data: str):
    username = data[data.find("'login': ")+9:data.find(",")]
    data = data[data.find(",")+1:]
    email = data[data.find("'email': ")+9:data.find(",")]
    data = data[data.find(",")+1:]
    password = data[data.find("'password': ")+12:data.find("}")]
    return username.replace("'", ""), email.replace("'", ""), password.replace("'", "")

def verify_entry_validity(username: str, email: str, password: str):
    if any(character in username for character in INVALID_CHARACTERS):
        return False, "Username is invalid - prohibited characters used"
    if any(character in email for character in INVALID_CHARACTERS):
        return False, "Email is invalid - prohibited characters used"
    if "@" not in email:
        return False, "Email is invalid - @?"
    if any(character in username for character in INVALID_CHARACTERS):
        return False, "Password is invalid - prohibited characters used"
    return True, ""



REQUESTS = {"Hello": "Hello!", "Find": best_matches, SEND_FILE_REQUEST: SEND_FILE_APPROVE,
                SEND_FILE_SUCCESS: SEND_FILE_SUCCESS, SEND_FILE_FAIL: SEND_FILE_FAIL, DISCONNECT_MSG: "Bye!",
                "Register": "", "Login": "", "Question": "Answer", "How do I become a coder?": "ChatGPT(no)"}

