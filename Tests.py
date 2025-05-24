from CLIENT.Protocols.PacketProtocol import *
from CLIENT.Protocols.SecurityProtocol import create_private_key, generate_fernet_key
from CLIENT.Protocols.Protocol import pack_message
import sqlite3

def test_session_token_serialization():
    original = SessionToken("abc123", "deviceXYZ", "topSecret!")
    dumped = original.dump()
    loaded = SessionToken.load(dumped)

    assert loaded.session_code == original.session_code
    assert loaded.device_fingerprint == original.device_fingerprint
    assert loaded.secret == original.secret
    print("[✓] SessionToken serialization test passed.")

def test_packet_creation_and_dump():
    session_token = SessionToken("abc123", "deviceXYZ", "topSecret!")
    msg = "Hello World!"
    args = {"user_id": 42, "flag": True}

    packet = Packet.create(packet_type=Agent.Client, msg=msg, args=args, session_token=session_token)
    dumped = packet.dump()
    assert isinstance(dumped, str)
    print("[✓] Packet creation and dump test passed.")


def test_packet_full_cycle():
    session_token = SessionToken("abc123", "deviceXYZ", "topSecret!")
    msg = "Important Message"
    args = {"value": 12345}

    original_packet = Packet.create(packet_type=Agent.Client, msg=msg, args=args, session_token=session_token)
    dumped = original_packet.dump()
    reloaded = Packet.load(dumped, packet_type=Agent.Client)

    assert reloaded.body["msg"] == msg
    assert reloaded.body["args"] == args
    assert reloaded.header["packet_id"] == original_packet.header["packet_id"]
    assert isinstance(reloaded.header["session_token"], str) or reloaded.header.get("session_token") is not None
    print("[✓] Packet dump/load roundtrip test passed.")


def test_packet_parsing():
    # Setup
    rsa_key = create_private_key()
    fernet_key = generate_fernet_key()

    handler = PacketHandler(type=Agent.Server, rsa_key=rsa_key, fernet_key=fernet_key)

    # Create and simulate encrypting a message
    session_token = SessionToken("abc123", "deviceXYZ", "secret!")
    packet = Packet.create(packet_type=Agent.Client, msg="Hi", args={}, session_token=session_token)
    message = pack_message(packet, handler, EncryptionKey.RSA, rsa_key.public_key())  # Simulated encryption
    print(message)
    # Parse the message
    parsed, error = handler.parse(message[4:])
    assert parsed is not None
    assert parsed.body["msg"] == "Hi"
    print("[✓] PacketHandler parse test passed.")


def test_invalid_type_handling():
    handler = PacketHandler(type=Agent.Server, rsa_key=None, fernet_key=b"badkey" * 4)
    bad_msg = b"XX" + b"malformed"
    packet, error = handler.parse(bad_msg)
    assert packet is None
    print("[✓] Invalid type test passed.")


def test_encrypt_fernet():
    fernet_key = generate_fernet_key()
    msg = "Length of 12"
    print(encrypt_fernet(fernet_key, msg.encode()))



if __name__ == "__main__":
    connection = sqlite3.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    cursor.execute("UPDATE Songs SET resolution=? WHERE id = 2", (0.05,))

    connection.commit()
    connection.close()

