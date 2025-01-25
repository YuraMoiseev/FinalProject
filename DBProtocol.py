import sqlite3
from ConstantsAndLogging import *
from SecurityProtocol import hash_password, verify_password


def create_db_tables():
    # create users table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
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


def create_songs_table():
    # Create songs table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Songs (
        id INTEGER PRIMARY KEY,
        melodies BLOB,
        song_name TEXT NOT NULL,
        added_by INTEGER NOT NULL,
        FOREIGN KEY (added_by) REFERENCES Users (id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    ''')
    connection.commit()
    connection.close()


def create_requests_table():
    # Create requests table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Requests (
        id INTEGER PRIMARY KEY,
        song_name TEXT NOT NULL,
        description TEXT
        requester_id INTEGER NOT NULL,
        FOREIGN KEY (requester_id) REFERENCES Users (id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    ''')
    connection.commit()
    connection.close()


def create_my_requests_table():
    # Create my_requests table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS My_Requests (
        id INTEGER PRIMARY KEY,
        request_id INTEGER NOT NULL,
        requester_id INTEGER NOT NULL,
        FOREIGN KEY (request_id) REFERENCES Requests (id) ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (requester_id) REFERENCES Users (id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    ''')
    connection.commit()
    connection.close()


def register_client(data):
    try:
        username, email, password = parse_args(str(data))
        hashed_password = hash_password(password)
        valid, msg = verify_entry_validity(username, email, password)
        if not valid:
            return msg
        connection = sqlite3.connect(DB_FILE_NAME)
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
        connection = sqlite3.connect(DB_FILE_NAME)
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


def add_song(song_name, midi_file_path, added_by):
    # Connect to the database
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    # Read the file in binary mode
    with open(midi_file_path, 'rb') as file:
        blob_data = file.read()

    # Insert the data into the Songs table
    cursor.execute('''
        INSERT INTO Songs (melodies, song_name, added_by)
        VALUES (?, ?, ?);
        ''', (blob_data, song_name, added_by))

    connection.commit()
    connection.close()


def add_request(song_name, description, added_by):
    # Connect to the database
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    # Insert the data into the Requests table
    cursor.execute('''
        INSERT INTO Requests (song_name, description, added_by)
        VALUES (?, ?, ?);
        ''', (song_name, description, added_by))

    connection.commit()
    connection.close()

def remove_request(request_id):
    # Connect to the database
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    # Insert the data into the Songs table
    cursor.execute('''
            DELETE FROM Requests WHERE id = ?;
            ''', request_id)

    connection.commit()
    connection.close()


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