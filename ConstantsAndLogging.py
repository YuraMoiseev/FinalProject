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

POP_UP_LABEL1: str = "There has been found a session associated with your device. Do you want to log in via the existing session?"
POP_UP_LABEL2: str = "Choose one of the options!"
POP_UP_LABEL3: str = "Do you want to save the existing session to log into the account without having to enter credentials?"


DELIMITER = b''

BUTTON_STYLE_SHEET: str = '''QPushButton {
                    font: 14pt "Arial";
border-radius: 15px;
border: 2px solid #00ff00;
color: #00ff00;
padding-top: 10px;
padding-bottom: 10px;
padding-left: 20px;
padding-right: 20px; 
                    }
QPushButton:hover {
                    font: 14pt "Arial";
border-radius: 15px;
border: 2px solid #00b300;
color: #00b300;
padding-top: 10px;
padding-bottom: 10px;
padding-left: 20px;
padding-right: 20px; 
                    }
QPushButton:pressed {
                    font: 14pt "Arial";
border-radius: 15px;
border: 2px solid #007000;
color: #008000;
padding-top: 10px;
padding-bottom: 10px;
padding-left: 20px;
padding-right: 20px; 
                    }

'''

ENTRY_STYLE_SHEET: str = '''font: 14pt "Arial";
border-radius: 5px;
border: 2px solid #00ff00;
color: #00ff00;'''

LABEL_STYLE_SHEET: str = '''
    font: 14pt "Arial";
    border-radius: 15px;
    color: #00ff00; 
    '''

ERROR_LABEL_STYLE_SHEET: str = '''
    font: 14pt "Arial";
    border-radius: 15px;
    color: #ff0000; 
    '''

DROP_FILE_STYLE_SHEET: str = '''
QLabel
    {
    font: 14pt "Arial";
    border-radius: 15px;
    color: #00ff00; 
    }
QLabel:hover
    {
    font: 14pt "Arial";
    border-radius: 15px;
    color: #00b300;
    }
'''

DB_FILE_NAME = "DataBases.db"

SECRET_KEY = b"Something_that_is_here_now_but_will_be_securely_stored_later"  # Keep this secret!

# prepare Log file
LOG_FILE = 'LOG.log'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def write_to_log(msg):
    logging.info(msg)
    print(msg)

