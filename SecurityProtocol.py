from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from ConstantsAndLogging import FORMAT, write_to_log
from argon2 import PasswordHasher

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
        write_to_log("[SECURITY_PROTOCOL] message decryption failed with exception {}".format(e))
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
