# General Constants
CLIENT_HOST: str = "127.0.0.1"
SERVER_HOST: str = "0.0.0.0"
PORT: int = 55555
BUFFER_SIZE: int = 1024
HEADER_LEN: int = 4
FORMAT: str = 'utf-8'
DISCONNECT_MSG: str = "EXIT"


# Request/Response messages
REG_FAIL_USERNAME: str = "Username/Email is already taken"
REG_SUCCESS: str = "User registered successfully"
LOGIN_FAIL: str = "Login failed"
LOGIN_SUCCESS: str = "Login successful"
LOGOUT_MSG: str = "Logout"

REG_MSG: str = "Registration request received"
SEARCH_SONG_REQUEST: str = "Song"
SEARCH_SONG_APPROVE: str = "Approve"
SEND_FILE_SUCCESS: str = "Wav file successfully transferred"
SEND_FILE_FAIL: str = "Could not transfer wav file"

POP_UP_LABEL1: str = "There has been found a session associated with your device. Do you want to log in via the existing session?"
POP_UP_LABEL2: str = "Choose one of the options!"
POP_UP_LABEL3: str = "Do you want to save the existing session to log into the account without having to enter user data?"
ERROR_MSGS = ["Error", "error", "Server workflow terminated"]


# Security
KEY_ROTATION_COUNTDOWN: int = 100

INVALID_CHARACTERS = [",", "{", "}"]

DELIMITER = b"||"
SESSION_TOKEN_DELIMITER = "_"

# GUI Styles

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
    background-color: #000000
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

TABLE_STYLE_SHEET = """
    QTableWidget {
        background-color: #000000;
        color: #00ff00; 
    }
    QHeaderView {
        background-color: #000000;
        color: #00ff00;
    }
    QHeaderView::section {
        background-color: #000000;
        color: #00ff00; 
        padding: 4px;
        border: 1px solid #00ff00;
    }
    QTableCornerButton::section {
        background-color: #000000;
        border: 1px solid #00ff00;
    }
"""


# Recording audio
recording_path: str = "temp/recording.wav"
seconds: int = 5
chunk: int = 1024  # Record in chunks of 1024 samples
channels: int = 1
fs: int = 44100  # Record at 44100 samples per second

