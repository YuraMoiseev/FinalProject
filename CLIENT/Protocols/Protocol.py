# Libraries
import socket
import os

# Local
from .PacketProtocol import *
from .SecurityProtocol import *
from CLIENT.config_utils.config import HEADER_LEN, BUFFER_SIZE


def pack_message(packet: Packet, packet_handler: PacketHandler, enc_key: IntFlag, public_key) -> bytes:
    try:
        """Create a valid protocol message and encrypt it using Fernet or RSA, will be sent by client, with length field"""
        if enc_key & DumpType.Short:
            request_body = packet.short_dump()
        else:
            request_body = packet.dump()
        if enc_key & EncryptionKey.RSA:
            request = f"{bin(int(enc_key))[2:]:04}".encode(FORMAT) + encrypt_rsa(public_key, request_body.encode(FORMAT))
        else:
            request = f"{bin(int(enc_key))[2:]:04}".encode(FORMAT) + encrypt_fernet(packet_handler.fernet_key, request_body.encode(FORMAT))
        return f"{len(request):0{HEADER_LEN}d}".encode(FORMAT) + request
    except Exception as e:
            write_to_log("[PROTOCOL] Exception on packing a message: {}".format(e))
            return False


def get_complete_file_path(file_type, file_name, dir):
    project_folder = os.getcwd()  # Get the project folder path
    os.makedirs(dir, exist_ok=True)  # Ensure the directory exists
    unique_id = uuid.uuid4().hex  # Generate a unique identifier
    file_path = os.path.join(project_folder, dir, f"{file_name}_{unique_id}.{file_type}")
    return file_path


def receive_file(client_socket, file_type, packet_handler=None):
    initial_timeout = client_socket.timeout
    try:
        print("Packet Handler:" + packet_handler.fernet_key)
        client_socket.settimeout(None) # Set a bigger timeout to avoid transmission issues
        file_name = get_complete_file_path(file_type, "file", "../../SERVER/ServerFiles")
        # Read the file size as a string until the newline character
        file_size_bytes = b""
        while not file_size_bytes.endswith(b"\n"):
            chunk = client_socket.recv(1)
            if not chunk:
                write_to_log("[PROTOCOL] file transfer - failed to read file size from the client.")
                return False, ""
            file_size_bytes += chunk
        # Convert the file size from string to integer
        file_size = int(file_size_bytes.decode(FORMAT).strip())
        if file_size == 0:
            write_to_log("[PROTOCOL] file transfer - file size is 0, file not saved")
            return True, file_name
        bytes_received = b""
        while len(bytes_received) < file_size:
            # Calculate remaining bytes to read
            remaining_bytes = file_size - len(bytes_received)
            # If there are less remaining bytes than the general buffer size, choose a corresponding buffer size
            bytes_to_read = min(BUFFER_SIZE, remaining_bytes)

            # Read the next chunk
            bytes_read = client_socket.recv(bytes_to_read)
            if not bytes_read:
                # Unexpected disconnection
                write_to_log("[PROTOCOL] file transfer - connection lost before file transfer was complete.")
                return False, ""
            # Write to file and update received byte count
            bytes_received += bytes_read
        with open(file_name, 'wb') as f:
            f.write(decrypt_fernet(packet_handler.fernet_key, bytes_received))

        client_socket.settimeout(initial_timeout)
        return True, file_name
    except Exception as e:
        client_socket.settimeout(initial_timeout)
        write_to_log(f"[PROTOCOL] exception file transfer - {e}")
        return False, ""


def send_file(file_name: str, sock, packet_handler: PacketHandler = None) -> bool:
    try:
        # Encrypt the whole thing
        encrypted_bytes = b""
        with open(file_name, 'rb') as f:
            encrypted_bytes = encrypt_fernet(packet_handler.fernet_key, f.read())
        # Get the size of the file
        file_size = len(encrypted_bytes)

        # Send the file size as a string followed by a newline
        sock.send(f"{file_size}\n".encode(FORMAT))

        # Send the file data
        for i in range(file_size//BUFFER_SIZE + 1):
            if (i+1)*BUFFER_SIZE < file_size:
                bytes_read = encrypted_bytes[i*BUFFER_SIZE:(i+1)*BUFFER_SIZE]
            else:
                bytes_read = encrypted_bytes[i*BUFFER_SIZE:]
                # File transmission is done
                sock.send(bytes_read)
                break
            sock.send(bytes_read)

        # Log the file transfer
        write_to_log(f"[CLIENT_BL] sent {sock.getsockname()} file {file_name}")
        return True

    except Exception as e:
        write_to_log("[CLIENT_BL] Exception on send: {}".format(e))
        sock.send(f"{0}\n".encode())
        sock.send(b"0")
        return False


def receive_msg(my_socket: socket, packet_handler:PacketHandler) -> tuple[bool, Packet, str]:
    """Decrypt and extract message from protocol, without the length field
       If length field does not include a number, returns False, "Error" """
    try:
        header = my_socket.recv(HEADER_LEN).decode(FORMAT)
        length = int(header)
        if length > 0:
            packet_str = my_socket.recv(length)
            packet, parse_msg = packet_handler.parse(packet_str)
        else:
            return False, Packet.create(msg=""), "Error"

        return True, packet, parse_msg

    except socket.timeout:
        return False, Packet.create(msg =""), "Socket Timeout"

    except (socket.error, ConnectionResetError):
        return False, Packet.create(msg =""), "Server workflow terminated"

    except Exception as e:
        # write_to_log("[PROTOCOL] receive msg failed with exception {}".format(e))
        return False, Packet.create(msg = ""), str(e)


def receive_key(my_socket:socket):
    str_header = my_socket.recv(HEADER_LEN).decode(FORMAT)
    length = int(str_header)
    if length > 0:
        pem = my_socket.recv(length).decode(FORMAT).encode(FORMAT)
        key = load_pem_public_key(pem)
        return key



