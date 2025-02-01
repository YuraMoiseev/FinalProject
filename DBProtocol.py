import sqlite3
import traceback
from ConstantsAndLogging import *
from SecurityProtocol import hash_password, verify_password, hash_device_id
import ast
import time


def create_db_tables():
    create_users_table()
    create_login_table()
    create_requests_table()
    create_sessions_table()
    create_songs_table()


def create_users_table():
    # create users table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY,
        is_admin BOOLEAN NOT NULL,
        login TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    );
    ''')
    connection.commit()
    connection.close()


def create_login_table():
    # create logins table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Logins (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            attempts INTEGER DEFAULT 0,
            last_attempt TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE ON UPDATE CASCADE
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
        artist_name TEXT NOT NULL,
        description TEXT,
        midi_audio_file BLOB,
        requester_id INTEGER NOT NULL,
        FOREIGN KEY (requester_id) REFERENCES Users (id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    ''')
    connection.commit()
    connection.close()


def create_sessions_table():
    # Create requests table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sessions (
        id INTEGER PRIMARY KEY,
        device_id_hash TEXT,
        keep_in_sleep BOOLEAN NOT NULL,
        is_running BOOLEAN NOT NULL,
        last_action TIMESTAMP,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (id)
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_device ON Sessions (device_id_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_id ON Sessions (id);")

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
            'INSERT INTO Users (is_admin, login, email, hashed_password) VALUES (?, ?, ?, ?)',
            (False, username, email, hashed_password)
        )
        connection.commit()
        connection.close()
        return REG_SUCCESS
    except Exception as e:
        write_to_log("[DB_PROTOCOL] - exception on registering a client - {}".format(e))


def login_client(username_or_email, password):
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        cursor.execute("SELECT id, hashed_password FROM Users WHERE login = ? OR email = ?", (username_or_email, username_or_email))
        result = cursor.fetchone()

        if result is None:
            return LOGIN_FAIL + " - no such user was found in database", None # None is a placeholder to generalize the cases of interaction with client without session

        hashed_password = result[1]
        user_id = result[0]
        connection.commit()
        connection.close()
        account_lock_time = is_account_locked(user_id)

        if account_lock_time[0]:
            return f"{LOGIN_FAIL} - the password for this user was entered too many times. Try again in {account_lock_time[1]//60} minutes and {account_lock_time[1]%60} seconds", None

        if verify_password(hashed_password, password):
            reset_failed_attempts(user_id)
            return LOGIN_SUCCESS, user_id # Return user ID for future reference

        else:
            record_failed_attempt(user_id)
            return LOGIN_FAIL + " - incorrect password", None

    except Exception as e:
        write_to_log("[DB_PROTOCOL] - exception on checking password - {}".format(e))
        return LOGIN_FAIL, None


def record_failed_attempt(user_id):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    cursor.execute("SELECT attempts FROM Logins WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row:
        attempts = row[0] + 1
        cursor.execute("UPDATE Logins SET attempts = ?, last_attempt = ? WHERE user_id = ?",
                       (attempts, round(time.time()), user_id))
    else:
        cursor.execute("INSERT INTO Logins (user_id, attempts, last_attempt) VALUES (?, ?, ?)",
                       (user_id, 1, round(time.time())))

    connection.commit()
    connection.close()


def is_account_locked(user_id, failed_attempts=10, lockout_time=600):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    cursor.execute("SELECT attempts, last_attempt FROM Logins WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    connection.close()

    if row and row[0] >= failed_attempts:  # Failed attempts amount exceeded
        last_attempt_time = row[1]
        time_left = lockout_time - (time.time() - last_attempt_time)
        if time_left > 0:
            return True, time_left  # Account is locked for ... more seconds
    return False, 0 # Account is not locked


def reset_failed_attempts(user_id):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM Logins WHERE user_id = ?", (user_id,))
    connection.commit()
    connection.close()


def start_session(user_id, device_id, keep_in_sleep):
    """Creates a new session for a user and returns the session ID."""
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    device_id_hash = device_id_hash = hash_device_id(device_id) # Make a hash of the device id for additional security

    timestamp = int(time.time())  # Current UNIX timestamp

    cursor.execute("""
        INSERT INTO Sessions (device_id_hash, keep_in_sleep, is_running, last_action, user_id) 
        VALUES (?, ?, 1, ?, ?)
    """, (device_id_hash, keep_in_sleep, timestamp, user_id))

    session_id = cursor.lastrowid  # Get the auto-incremented session ID

    connection.commit()
    connection.close()

    return session_id  # Return session ID for reference


def delete_session(session_id):
    """Deletes a session by its ID."""
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()

        cursor.execute("DELETE FROM Sessions WHERE id = ?", (session_id,))

        connection.commit()
        connection.close()
        return "Success"
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] deleting session failed due to the exception {e}")
        return "Fail"


def update_last_action(session_id):
    """Updates the last_action timestamp for a session."""
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    timestamp = int(time.time())  # Current timestamp
    cursor.execute("UPDATE Sessions SET last_action = ? WHERE id = ?", (timestamp, session_id))

    connection.commit()
    connection.close()


def login_with_data(data):
    try:
        username_or_email, password, device_id, keep_in_sleep = parse_args(data)
        login_msg, user_id = login_client(username_or_email, password)
        is_success = login_msg == LOGIN_SUCCESS
        session_id = None
        if is_success:
            session_id = start_session(user_id, device_id, keep_in_sleep)
        return login_msg, session_id
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] login with session failed due to the exception {e}")
        # write_to_log(traceback.format_exc())
        return "", None


def login_with_old_session(data):
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()

        device_id = parse_args(data)[0]

        device_id_hash = hash_device_id(device_id)

        cursor.execute("SELECT id FROM Sessions WHERE device_id_hash = ?", (device_id_hash,))
        result = cursor.fetchone()

        # If the session was found, log the user in
        if result is not None:
            return LOGIN_SUCCESS, result
        # Else block the user from entering
        else:
            return LOGIN_FAIL + " - session was not found", None

    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] login with old session failed due to the exception {e}")
        return "", None


def add_request(data, session_id):
    try:
        song_name, artist_name, link, description, file_path = parse_args(data)
        # Connect to the database
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()

        if file_path is not None:
            # Read the file in binary mode
            with open(file_path, 'rb') as file:
                blob_data = file.read()
        else:
            blob_data = None

        # Retrieve the user id from the session
        cursor.execute("SELECT user_id FROM Sessions WHERE id = ?", (session_id,))
        user_id = cursor.fetchone()
        # Insert the data into the Requests table
        cursor.execute('''
            INSERT INTO Requests (song_name, artist_name, link, description, user_id, midi_audio_file)
            VALUES (?, ?, ?, ?, ?, ?);
            ''', (song_name, artist_name, link, description, user_id, blob_data))

        connection.commit()
        connection.close()
        return True
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] add request failed due to the exception {e}")
        return False



def add_song(data, user_id):
    midi_file_path, song_name, artist_name = parse_args(data)
    # Connect to the database
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    # Read the file in binary mode
    with open(midi_file_path, 'rb') as file:
        blob_data = file.read()

    # Insert the data into the Songs table
    cursor.execute('''
        INSERT INTO Songs (melodies, song_name, artist_name, added_by)
        VALUES (?, ?, ?, ?);
        ''', (blob_data, song_name, artist_name, user_id))

    connection.commit()
    connection.close()


def remove_request(request_id):
    # Connect to the database
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    # Insert the data into the Songs table
    cursor.execute('''
            DELETE FROM Requests WHERE id = ?;
            ''', (request_id,))

    connection.commit()
    connection.close()


def parse_args(data: str):
    # Convert the string representation of a dictionary back to a Python dictionary
    dictionary = ast.literal_eval(data)
    # Return the values as a tuple
    return tuple(dictionary.values())


def verify_entry_validity(username: str, email: str, password: str):
    if any(character in username for character in INVALID_CHARACTERS):
        return False, "Username is invalid - prohibited characters used"
    if any(character in email for character in INVALID_CHARACTERS):
        return False, "Email is invalid - prohibited characters used"
    if "@" not in email:
        return False, "Email is invalid - @?"
    if any(character in password for character in INVALID_CHARACTERS):
        return False, "Password is invalid - prohibited characters used"
    return True, ""