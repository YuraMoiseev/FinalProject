# Libraries
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.fernet import Fernet
from argon2 import PasswordHasher
import hmac
import hashlib
import secrets
import string

# Local
from SERVER.config_utils.config import FORMAT, SECRET_KEY
from SERVER.config_utils.utils import write_to_log

def to_bytes(data):
    if not isinstance(data, bytes):
        data = data.encode(FORMAT)
    return data

def create_private_key(public_exponent=65537, key_size=2048):
    return rsa.generate_private_key(public_exponent=public_exponent, key_size=key_size)

def create_signature(private_key, data):
    try:
        data = to_bytes(data)
        # Create the signature
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] signature creation failed with exception {}".format(e))
        return None

def verify_signature(public_key, signature, data):
    try:
        data = to_bytes(data)
        # Verify the signature
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print("Signature is valid.")
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] signature verification failed with exception {}".format(e))

def encrypt_rsa(public_key, data):
    try:
        data = to_bytes(data)
        # Encrypt the message
        encrypted_data = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_data
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] message encryption (RSA) failed with exception {}".format(e))

def decrypt_rsa(private_key, encrypted_data):
    try:
        encrypt_data = to_bytes(encrypted_data)
        # Decrypt the message
        decrypted_data = private_key.decrypt(
            encrypt_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_data
    except Exception as e:
        write_to_log(f"[SECURITY_PROTOCOL] message decryption (RSA) failed with exception {e} with data {encrypted_data}")
        return "Error"

def load_pem(public_key):
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return public_pem

def load_key(pem):
    key = load_pem_public_key(pem)
    return key

def hash_password(password, time_cost=3, memory_cost=131072, parallelism=4):
    try:
        ph = PasswordHasher(time_cost=time_cost, memory_cost=memory_cost, parallelism=parallelism)
        return ph.hash(password)
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] password hashing failed with exception - {}".format(e))
        return None

def verify_password(hashed_password, password):
    try:
        ph = PasswordHasher()
        ph.verify(hashed_password, password)
        return True
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] password verification failed with exception - {}".format(e))
        return False

def generate_session_code(length=16):
    # Define possible characters (letters + digits)
    alphabet = string.ascii_letters + string.digits
    # Generate a random code
    session_code = ''.join(secrets.choice(alphabet) for _ in range(length))
    return session_code

def hash_session_code(session_code):
    return hmac.new(SECRET_KEY, session_code.encode(), hashlib.sha256).hexdigest()


def generate_fernet_key():
    return Fernet.generate_key()


def encrypt_fernet(fernet_key: bytes, data: bytes) -> bytes:
    """
    Encrypts the given data using the provided Fernet key.
    
    Args:
        fernet_key: A Fernet key (must be 32 url-safe base64-encoded bytes).
        data: The data to encrypt (as bytes).
    
    Returns:
        The encrypted data (ciphertext) as bytes.
    """
    try:
        f = Fernet(fernet_key)
        encrypted_data = f.encrypt(data)
        return encrypted_data
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] message encryption (Fernet) failed with exception {}".format(e))

def decrypt_fernet(fernet_key: bytes, encrypted_data: bytes) -> bytes:
    """
    Decrypts the given encrypted data using the provided Fernet key.
    
    Args:
        fernet_key: A Fernet key (must be 32 url-safe base64-encoded bytes).
        encrypted_data: The encrypted data (as bytes).
    
    Returns:
        The decrypted data (plaintext) as bytes.
    """
    try:
        f = Fernet(fernet_key)
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] message encryption (Fernet) failed with exception {}".format(e))
