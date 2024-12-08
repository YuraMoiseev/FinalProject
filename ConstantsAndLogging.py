import logging

# my ip - 10.81.206.63
CLIENT_HOST: str = "127.0.0.1"
SERVER_HOST: str = "0.0.0.0"
PORT: int = 55555
BUFFER_SIZE: int = 1024
HEADER_LEN: int = 4
FORMAT: str = 'utf-8'
DISCONNECT_MSG: str = "EXIT"

INVALID_CHARACTERS = [",", "{", "}"]
REG_FAIL_USERNAME: str = "Username/Email is already taken"
REG_SUCCESS: str = "User registered successfully"
LOGIN_FAIL: str = "Login failed"
LOGIN_SUCCESS: str = "Login successful"

REG_MSG: str = "Registration request received"
SEND_FILE_REQUEST: str = "Song"
SEND_FILE_APPROVE: str = "Approve"
SEND_FILE_SUCCESS: str = "Wav file successfully transferred"
SEND_FILE_FAIL: str = "Could not transfer wav file"



# prepare Log file
LOG_FILE = 'LOG.log'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def write_to_log(msg):
    logging.info(msg)
    print(msg)
