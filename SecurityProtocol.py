import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ConstantsAndLogging import FORMAT, write_to_log


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

def encrypt_msg(public_key, data):
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
        write_to_log("[SECURITY_PROTOCOL] message encryption failed with exception {}".format(e))

def decrypt_msg(private_key, encrypted_data):
    try:
        encrypted_data = to_bytes(encrypted_data)
        # Decrypt the message
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_data
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] message decryption failed with exception {}".format(e))

def hash_password(password, key_length=32, salt=None, salt_size=16, iterations=100_000):
    """
        Hashes a password using PBKDF2HMAC.

        :param password: The password to hash.
        :param key_length: Desired length of the derived key.
        :param salt: Optional; provide a salt if you want to reuse one.
        :param salt_size: Size of the salt in bytes if generating a new one.
        :param iterations: Number of iterations for the hashing algorithm.
        :return: A tuple of (hashed_password, salt) or None if hashing fails.
        """
    try:
        password = to_bytes(password)
        if not salt:
            salt = os.urandom(salt_size)
        kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=iterations,
        )
        hashed_password = kdf.derive(password)
        return hashed_password, salt
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] password hashing failed with exception {}".format(e))
        return None

def check_passwords(password, hashed_password, salt, key_length=32, iterations=100_000):
    """
       Verifies if a provided password matches the hashed password.

       :param password: The password to check.
       :param hashed_password: The stored hashed password.
       :param salt: The salt used during the hashing process.
       :param key_length: Length of the derived key.
       :param iterations: Number of iterations for the hashing algorithm.
       :return: True if the passwords match, False otherwise.
       """
    try:
        password = to_bytes(password)
        hashed_password = to_bytes(hashed_password)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=iterations,
        )
        kdf.verify(password, hashed_password)
        return True
    except Exception as e:
        write_to_log("[SECURITY_PROTOCOL] password check failed with exception {}".format(e))
        return False
