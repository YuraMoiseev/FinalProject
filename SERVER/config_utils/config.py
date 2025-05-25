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

DELIMITER = b"||"
SESSION_TOKEN_DELIMITER = "_"

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

DB_FILE_NAME = "C:/Users/Ymois/PycharmProjects/FinalProject/SERVER/Protocols/DataBases.db"

REQUESTS_COLUMNS = {'Id': None, 'Song Name':None, 'Artist':None, 'Link':None, 'Description':None, 'File Type':None, 'Requester':None, 'Reject':None, 'Accept':None}
USERS_COLUMNS = {'Id':None, 'Username':None, 'Admin':None}


VirtualEnv = "C:/Users/Ymois/PycharmProjects/FinalProject/venv/Scripts/activate"

# Weighing and similarity constants
"""
For deeper understanding and reasoning behind the constants - please read the MelodyComparison.pdf file
1. Each *s* weighed dist is multiplied by *b*
2. Forcing weighed dist at *x0* to be equal to *y0*
3. Weighted additionally when combining distances
4. a - how fast the dist goes down to 0 at values smaller than the x0 (just a huge value, prolly won't need it but ehh why not ._. )
"""
WASC = {
    "d": {
        "s": 2,
        "x0": 0.02,
        "y0": 0.1,
        "w": 25,
        "a": 3,
        "b": 10
    },
    "n": {
        "s": 5,
        "x0": 0.05,
        "y0": 0.1,
        "w": 10,
        "a": 2,
        "b": 10
    },
    "t": {
        "s": 0.3,
        "x0": 0.1,
        "y0": 0.1,
        "w": 3,
        "a": 5,
        "b": 10
    }
}

