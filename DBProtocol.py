import sqlite3

from ConstantsAndLogging import *
from MusicalAnalysis import MidiAnalyzer
from SecurityProtocol import hash_password, verify_password, hash_device_id
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
        hashed_password TEXT NOT NULL,
        successful_additions INTEGER NOT NULL,
        failed_additions INTEGER NOT NULL
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
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    # Create songs table in DB
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Songs (
        id INTEGER PRIMARY KEY,
        melodies BLOB,
        song_name TEXT NOT NULL,
        artist_name TEXT NOT NULL,
        added_by INTEGER NOT NULL,
        FOREIGN KEY (added_by) REFERENCES Users (id) ON UPDATE CASCADE
    );
    ''')

    # Create a trigger to set added_by to -1 when a user is deleted
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS before_user_delete
        BEFORE DELETE ON Users
        FOR EACH ROW
        BEGIN
            UPDATE Songs
            SET added_by = -1
            WHERE added_by = OLD.id;
        END;
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
        link TEXT,
        description TEXT,
        midi_audio_file BLOB,
        file_type TEXT,
        requester TEXT NOT NULL,
        FOREIGN KEY (requester) REFERENCES Users (login) ON DELETE CASCADE ON UPDATE CASCADE
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



def create_responses_table():
    # Create requests table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Responses (
        id INTEGER PRIMARY KEY,
        is_approved BOOLEAN NOT NULL,
        description TEXT,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (id)
    )
    """)

    connection.commit()
    connection.close()


def create_searches_table():
    # Create requests table in DB
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sessions (
        id INTEGER PRIMARY KEY,
        results JSONB,
        timestamp INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (id)
    )
    """)

    connection.commit()
    connection.close()


def register_client(data):
    try:
        username, email, password = data["login"], data["email"], data["password"]
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
            'INSERT INTO Users (is_admin, login, email, hashed_password, successful_additions, failed_additions) VALUES (?, ?, ?, ?, 0, 0)',
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
            return LOGIN_FAIL + " - no such user was found in database", None

        hashed_password = result[1]
        user_id = result[0]
        connection.commit()
        connection.close()
        account_lock_time = is_account_locked(user_id)

        if account_lock_time[0]:
            minutes, seconds = account_lock_time[1]//60, account_lock_time[1]%60//1
            return f"{LOGIN_FAIL} - the password for this user was entered too many times. Try again in {minutes} minutes and {seconds} seconds", None

        if verify_password(hashed_password, password):
            reset_failed_attempts(user_id)
            return LOGIN_SUCCESS, user_id # Return user id for session creation

        else:
            record_failed_attempt(user_id)
            return LOGIN_FAIL + " - incorrect password", None

    except Exception as e:
        write_to_log("[DB_PROTOCOL] - exception on checking password - {}".format(e))
        return LOGIN_FAIL, None


def toggle_client_status(user_id, is_admin=True):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute("UPDATE Users SET is_admin = ? WHERE id = ?",
                   (is_admin, user_id))
    connection.commit()
    connection.close()


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


def start_session(user_id, device_id):
    """Creates a new session for a user and returns the session ID."""
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    device_id_hash = hash_device_id(device_id) # Make a hash of the device id for additional security

    timestamp = int(time.time())  # Current UNIX timestamp

    cursor.execute("""
        INSERT INTO Sessions (device_id_hash, is_running, last_action, user_id) 
        VALUES (?, ?, ?, ?)
    """, (device_id_hash, True, timestamp, user_id))

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


def handle_session_limit(session_id):
    """Checks the last action of the session. Deletes if the time limit was exceeded, updates the last action if not"""
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()

        timestamp = int(time.time())  # Current UNIX timestamp

        cursor.execute("SELECT last_action, is_running FROM Sessions WHERE id = ?", (session_id,))
        last_action, is_running = cursor.fetchone()
        connection.commit()
        connection.close()

        time_window_seconds = 1800 + 1800 * 23 * int(is_running) # create a delta of how much time the session is available based off of if it's locked or not

        if last_action + time_window_seconds < timestamp:
            delete_session(session_id)
            return False
        else:
            update_last_action(session_id)
            return True

    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] handling session failed due to the exception {e}")
        return False


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
        username_or_email, password, device_id = data["login"], data["password"],  data["device_id"]
        login_msg, user_id = login_client(username_or_email, password)
        is_success = login_msg == LOGIN_SUCCESS
        session_id = None
        if is_success:
            session_id = start_session(user_id, device_id)

        return login_msg, session_id
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] login with session failed due to the exception {e}")
        return "", None


def login_with_old_session(data):
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()

        device_id = data["device_id"]

        device_id_hash = hash_device_id(device_id)
        cursor.execute("SELECT id, is_running FROM Sessions WHERE device_id_hash = ?", (device_id_hash,))
        result = cursor.fetchone()
        # If the session was found, and it has not expired, log the user in
        if result is not None:
            session_id = result[0]
            is_running = result[1]
            if handle_session_limit(session_id):
                toggle_session_state(session_id, True)
                update_last_action(session_id)
                return LOGIN_SUCCESS, session_id # Also save the session id for future reference
            elif is_running:
                return LOGIN_FAIL + " - the session is already taken", None
            else:
                return LOGIN_FAIL + " - the session has expired", None
        # Else block the user from entering
        else:
            return LOGIN_FAIL + " - session was not found", None

    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] login with old session failed due to the exception {e}")
        return "", None


def add_request(data, session_id, file_path=None, file_type=None):
    try:
        song_name, artist_name, link, description = data["name"], data["artist"], data["link"], data["description"]
        # Connect to the database
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        if file_path is not None:
            # Read the file in binary mode
            with open(file_path, 'rb') as file:
                blob_data = file.read()
        else:
            blob_data = b""

        # Retrieve the user id from the session
        cursor.execute("SELECT user_id FROM Sessions WHERE id = ?", (session_id,))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT login FROM Users WHERE id = ?", (user_id,))
        user_name = cursor.fetchone()[0]
        # Insert the data into the Requests table
        cursor.execute('''
            INSERT INTO Requests (song_name, artist_name, link, description, requester, midi_audio_file, file_type)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            ''', (song_name, artist_name, link, description, user_name, blob_data, file_type))

        connection.commit()
        connection.close()
        return "Success"
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] add request failed due to the exception {e}")
        return "Fail"


def update_request(data, file_path=None, file_type=None):
    try:
        song_name, artist_name, link, description, request_id, file_type = data["name"], data["artist"], data["link"], data["description"], data["id"], data["file_type"]
        # Connect to the database
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        if file_path == "_":
            # Insert the data into the Requests table
            cursor.execute('''
                        UPDATE Requests 
                        SET song_name = ?, artist_name = ?, link = ?, description = ?, file_type = ? 
                        WHERE id = ?;
                        ''', (song_name, artist_name, link, description, file_type, request_id))
            connection.commit()
            connection.close()
            return "Success"

        if file_path is not None:
            # Read the file in binary mode
            with open(file_path, 'rb') as file:
                blob_data = file.read()
        else:
            blob_data = b""

        # Insert the data into the Requests table
        cursor.execute('''
            UPDATE Requests 
            SET song_name = ?, artist_name = ?, link = ?, description = ?, midi_audio_file = ?, file_type = ? 
            WHERE id = ?;
            ''', (song_name, artist_name, link, description, blob_data, file_type, request_id))

        connection.commit()
        connection.close()
        return "Success"
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] add request failed due to the exception {e}")
        return "Fail"


def extract_file(table_name, file_path, row_id, column_file_name, column_file_type):
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        query = f"SELECT {column_file_name}, {column_file_type} FROM {table_name} WHERE id = ?"
        cursor.execute(query, (row_id,))
        # Fetch the BLOB data and file type
        result = cursor.fetchone()
        connection.close()
        if not result:
            write_to_log(f"No data found for row ID {row_id} in table {table_name}.")
            return False

        blob_data, file_type = result
        if not blob_data:
            write_to_log(f"No BLOB data found for row ID {row_id} in table {table_name}.")
            return False

        # Save the BLOB data to the specified file path
        if file_path:
            with open(file_path, 'wb') as file:
                file.write(blob_data)
            return True
        else:
            return False

    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] file extract failed due to the exception {e}")


def add_song(midi_file_path, song_name, artist_name, username):
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
        ''', (blob_data, song_name, artist_name, username))

    connection.commit()
    connection.close()


def toggle_session_state(session_id, is_running):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    cursor.execute("UPDATE Sessions SET is_running = ? WHERE id = ?", (is_running, session_id))

    connection.commit()
    connection.close()


def delete_request(request_id):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    cursor.execute('''
            DELETE FROM Requests WHERE id = ?;
            ''', (request_id,))

    connection.commit()
    connection.close()


def fetch_requests(offset, amount=10):
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()

        cursor.execute('''
                    SELECT id, song_name, artist_name, link, description, file_type, requester FROM Requests LIMIT ? OFFSET ?
                    ''', (amount, offset))
        rows = cursor.fetchall()


        # Convert rows to a list of dictionaries for easier handling
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]

        connection.close()
        return result
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] fetching requests failed due to the exception {e}")
        return None


def fetch_users(offset, amount=10):
    try:
        connection = sqlite3.connect(DB_FILE_NAME)
        cursor = connection.cursor()

        cursor.execute('''
                    SELECT id, login, is_admin FROM Users LIMIT ? OFFSET ?
                    ''', (amount, offset))
        rows = cursor.fetchall()

        # Convert rows to a list of dictionaries for easier handling
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]

        # Convert is_admin to bool
        for user in result:
            user['is_admin'] = bool(user['is_admin'])

        connection.close()
        return result
    except Exception as e:
        write_to_log(f"[DB_PROTOCOL] fetching users failed due to the exception {e}")
        return None


def fetch_songs(offset=0, amount=10):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''
                        SELECT song_name, artist_name, melodies FROM Songs LIMIT ? OFFSET ?
                        ''', (amount, offset))
    rows = cursor.fetchall()
    result_dict = {(song_name, artist_name): blob_data for song_name, artist_name, blob_data in rows}
    return result_dict


def fetch_song_names(offset=0, amount=10):
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''
                        SELECT song_name, artist_name FROM Songs LIMIT ? OFFSET ?
                        ''', (amount, offset))
    rows = cursor.fetchall()
    result_dict = {song_name: artist_name for song_name, artist_name in rows}
    return result_dict


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


if __name__ == "__main__":
    s = fetch_songs()
    file = list(s.values())[0]
    MA = MidiAnalyzer.load_midi_from_blob(file)
    # print(MA.note_sequence)
    # print(MA.timing_sequence)
    # print(MA.progression_sequence)
