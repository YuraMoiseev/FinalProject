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
    hashed_password TEXT NOT NULL,
    salt TEXT NOT NULL
    );
    ''')
    connection.commit()
    connection.close()

def register_client(data):
    try:
        username, email, password = parse_args(str(data))
        hashed_password, salt = hash_password(password)
        connection = sqlite3.connect("Users.db")
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM Users WHERE login = ? OR email = ?", (username, email))
        if cursor.fetchone() is not None:
            connection.commit()
            connection.close()
            return REG_FAIL_USERNAME
        cursor.execute(
            'INSERT INTO Users (login, email, hashed_password, salt) VALUES (?, ?, ?, ?)',
            (username, email, hashed_password, salt)
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
        cursor.execute("SELECT hashed_password, salt FROM Users WHERE login = ? OR email = ?", (username_or_email, username_or_email))
        result = cursor.fetchone()
        if result is None:
            return LOGIN_FAIL + " - no such user was found in database"
        hashed_password, salt = result
        connection.commit()
        connection.close()
        if check_passwords(password, hashed_password, salt):
            return LOGIN_SUCCESS
        else:
            # will change when the hashing is taught ._.
            return LOGIN_FAIL + " - incorrect password"
    except Exception as e:
        write_to_log("[PROTOCOL] - exception on checking password - {}".format(e))


def parse_args(data: str):
    data = data.strip()
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

