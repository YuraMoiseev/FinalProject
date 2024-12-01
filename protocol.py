import socket
import logging
# from cryptography.fernet import Fernet
# import sqlite3

# my ip - 10.81.206.63
CLIENT_HOST: str = "127.0.0.1"
SERVER_HOST: str = "0.0.0.0"
PORT: int = 55555
BUFFER_SIZE: int = 1024
HEADER_LEN: int = 4
FORMAT: str = 'utf-8'
DISCONNECT_MSG: str = "EXIT"
REG_MSG: str = "Registration request received"
SEND_FILE_REQUEST: str = "Song"
SEND_FILE_APPROVE: str = "Approve"
SEND_FILE_SUCCESS: str = "Wav file successfully transferred"
SEND_FILE_FAIL: str = "Count not transfer wav file"


def compare_melody(client_data, db_data):
    # will compare the entered melody to the melodies of some specific song in db
    pass


def best_matches(data):
    # will iterate through the database and compare the values, then will return the 10 closest matches
    pass


REQUESTS = {"Hello": "Hello!", "Find": best_matches, SEND_FILE_REQUEST:SEND_FILE_APPROVE, SEND_FILE_SUCCESS:SEND_FILE_SUCCESS, SEND_FILE_FAIL:SEND_FILE_FAIL, DISCONNECT_MSG: "Bye!"}

# prepare Log file
LOG_FILE = 'LOG.log'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_cmd(data):
    return data in REQUESTS


def create_request_msg(data) -> str:
    """Create a valid protocol message, will be sent by client, with length field"""
    request = ''
    if check_cmd(data):
        request += f"{len(data):0{HEADER_LEN}d}{data}"
    else:
        request = f"{len('Non-supported cmd'):0{HEADER_LEN}d}Non-supported cmd"
    return request


def create_response_msg(data) -> str:
    """Create a valid protocol message, will be sent by server, with length field"""
    if check_cmd(data):
        response = f"{len(REQUESTS[data]):0{HEADER_LEN}d}{REQUESTS[data]}"
    else:
        response = "Non-supported cmd"
    return response


def receive_msg(my_socket: socket) -> (bool, str):
    """Extract message from protocol, without the length field
       If length field does not include a number, returns False, "Error" """
    str_header = my_socket.recv(HEADER_LEN).decode(FORMAT)
    length = int(str_header)
    if length > 0:
        buf = my_socket.recv(length).decode(FORMAT)
    else:
        return False, "Error"

    return True, buf


# def create_users_table():
#     # create users table in DB
#     connection = sqlite3.connect("Users.db")
#     cursor = connection.cursor()
#     cursor.execute('''
#     CREATE TABLE IF NOT EXISTS Users (
#     id INTEGER PRIMARY KEY,
#     login TEXT UNIQUE NOT NULL,
#     password TEXT NOT NULL,
#     key TEXT NOT NULL
#     );
#     ''')
#     connection.commit()
#     connection.close()

#
# def generate_key():
#     return Fernet.generate_key()
#
#
# def encrypt_password_and_get_key(password):
#     key = generate_key()
#     cipher_suite = Fernet(key)
#     return cipher_suite.encrypt(password.encode()), key

#
# def register_client(data):
#     username, password = parse_args(str(data))
#     encrypt_pw, key = encrypt_password_and_get_key(password)
#     connection = sqlite3.connect("Users.db")
#     cursor = connection.cursor()
#     cursor.execute('INSERT INTO Users (login, password, key) VALUES (?,?,?)', (username, encrypt_pw, key))
#     connection.commit()
#     connection.close()


# def parse_args(data: str):
#     username = data[data.find("'login': ")+9:data.find(",")]
#     data = data[data.find(","):]
#     password = data[data.find("'password': ")+12:data.find("}")]
#     return username.replace("'", ""), password.replace("'", "")


def write_to_log(msg):
    logging.info(msg)
    print(msg)
