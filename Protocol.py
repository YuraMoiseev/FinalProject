import socket
from PacketProtocol import *
from SecurityProtocol import *
import os
import uuid


def compare_melody(client_data, db_data):
    # will compare the entered melody to the melodies of some specific song in db
    pass


def best_matches(data):
    # will iterate through the database and compare the values, then will return the 10 closest matches
    pass


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


# def create_response_msg(public_key, data) -> str:
#     """Encrypt and make the given protocol response valid, will be sent by server, with length field"""
#     response = encrypt_rsa(public_key, data)
#     if response is None:
#         response = b''
#     # return f"{len(str(response)):0{HEADER_LEN}d}".encode(FORMAT) + response
#     return f"{len(response):0{HEADER_LEN}d}".encode(FORMAT) + response


def get_complete_file_path(file_type, file_name, dir):
    project_folder = os.getcwd()  # Get the project folder path
    os.makedirs(dir, exist_ok=True)  # Ensure the directory exists
    unique_id = uuid.uuid4().hex  # Generate a unique identifier
    file_path = os.path.join(project_folder, dir, f"{file_name}_{unique_id}.{file_type}")
    return file_path


def receive_file(client_socket, file_type):
    initial_timeout = client_socket.timeout
    try:
        client_socket.settimeout(None) # Set a bigger timeout to avoid transmission issues
        file_name = get_complete_file_path(file_type, "file", "ServerFiles")
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
        bytes_received = 0
        with open(file_name, 'wb') as f:
            while bytes_received < file_size:
                # Calculate remaining bytes to read
                remaining_bytes = file_size - bytes_received
                # If there are less remaining bytes than the general buffer size, choose a corresponding buffer size
                bytes_to_read = min(BUFFER_SIZE, remaining_bytes)

                # Read the next chunk
                bytes_read = client_socket.recv(bytes_to_read)
                if not bytes_read:
                    # Unexpected disconnection
                    write_to_log("[PROTOCOL] file transfer - connection lost before file transfer was complete.")
                    return False, ""

                # Write to file and update received byte count
                f.write(bytes_read)
                bytes_received += len(bytes_read)
        client_socket.settimeout(initial_timeout)
        return True, file_name
    except Exception as e:
        client_socket.settimeout(initial_timeout)
        write_to_log(f"[PROTOCOL] exception file transfer - {e}")
        return False, ""


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
        return False, Packet.create(msg = ""), e


def receive_key(my_socket:socket):
    str_header = my_socket.recv(HEADER_LEN).decode(FORMAT)
    length = int(str_header)
    if length > 0:
        pem = my_socket.recv(length).decode(FORMAT).encode(FORMAT)
        key = load_pem_public_key(pem)
        return key



