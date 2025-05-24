import logging
import os
from .config import INVALID_CHARACTERS

def literal_bool(boo:str):
    if boo == "True" or boo == "1":
        return True
    return False

# prepare Log file
LOG_FILE = '../../LOG.log'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def write_to_log(msg):
    logging.info(msg)
    print(msg)


def is_file_present(file_name: str) -> bool:
    if not os.path.exists(file_name):
        write_to_log(f"[PROTOCOL] - file does not exist: {file_name}")
        return False
    return True


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

