import socket
import logging
from cryptography.fernet import Fernet
import sqlite3


# my ip - 10.81.206.63
CLIENT_HOST: str = "127.0.0.1"
SERVER_HOST: str = "0.0.0.0"
PORT: int = 55555
BUFFER_SIZE: int = 1024
HEADER_LEN: int = 4
FORMAT: str = 'utf-8'
DISCONNECT_MSG: str = "EXIT"

REG_FAIL: str = "Username is already taken."
REG_SUCCESS: str = "User registered successfully."
LOGIN_FAIL: str = "Login failed"
LOGIN_SUCCESS: str = "Login successful"

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


# prepare Log file
LOG_FILE = 'LOG.log'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_message(data):
    if ">" in data:
        return data[:data.index(">")], data[data.index(">")+1:]
    return data, None


def check_cmd(data):
    return parse_message(data)[0] in REQUESTS


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
    if check_cmd(data) and parse_message(data)[0]!="Register" and parse_message(data)[0]!="Login":
        response = REQUESTS[data]
    elif parse_message(data)[0] == "Register":
        response = register_client(parse_message(data)[1])
    elif parse_message(data)[0] == "Login":
        response = check_password(parse_message(data)[1])
    else:
        response = "Non-supported cmd"
    return f"{len(response):0{HEADER_LEN}d}{response}"


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


def create_users_table():
    # create users table in DB
    connection = sqlite3.connect("Users.db")
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    login TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    key TEXT NOT NULL
    );
    ''')
    connection.commit()
    connection.close()


def generate_key():
    return Fernet.generate_key()


def encrypt_password_and_get_key(password):
    key = generate_key()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(password.encode()), key


def encrypt_by_key(password, key):
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(password.encode())


def register_client(data):
    username, email, password = parse_args(str(data))
    encrypt_pw, key = encrypt_password_and_get_key(password)
    connection = sqlite3.connect("Users.db")
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM Users WHERE login = ? OR email = ?", (username, email))
    if cursor.fetchone() is not None:
        connection.commit()
        connection.close()
        return REG_FAIL
    cursor.execute(
        'INSERT INTO Users (login, email, password, key) VALUES (?, ?, ?, ?)',
        (username, email, encrypt_pw, key)
    )
    connection.commit()
    connection.close()
    return REG_SUCCESS


def check_password(data):
    username_or_email, none, password = parse_args(str(data))
    connection = sqlite3.connect("Users.db")
    cursor = connection.cursor()
    cursor.execute("SELECT password, key FROM Users WHERE login = ? OR email = ?", (username_or_email, username_or_email))
    result = cursor.fetchone()
    if result is None:
        return LOGIN_FAIL + " - no such user was found in database"
    encrypted_password, key = result
    connection.commit()
    connection.close()
    if encrypt_by_key(password, key) == encrypted_password:
        return LOGIN_SUCCESS
    else:
        # will change when the hashing is taught ._.
        return LOGIN_SUCCESS # + " - incorrect password"



def parse_args(data: str):
    username = data[data.find("'login': ")+9:data.find(",")]
    data = data[data.find(",")+1:]
    email = data[data.find("'email': ")+9:data.find(",")]
    data = data[data.find(",")+1:]
    password = data[data.find("'password': ")+12:data.find("}")]
    return username.replace("'", ""), email.replace("'", ""), password.replace("'", "")


def write_to_log(msg):
    logging.info(msg)
    print(msg)

REQUESTS = {"Hello": "Hello!", "Find": best_matches, SEND_FILE_REQUEST:SEND_FILE_APPROVE,
            SEND_FILE_SUCCESS:SEND_FILE_SUCCESS, SEND_FILE_FAIL:SEND_FILE_FAIL, DISCONNECT_MSG: "Bye!",
            "Register": "", "Login": "", "Question": "Answer", "How do I become a coder?": "ChatGPT(no)"}