# Libraries
import json
from enum import IntFlag
from dataclasses import dataclass, field
import uuid

# Local
from SERVER.config_utils.config import FORMAT, SESSION_TOKEN_DELIMITER, DELIMITER
from SERVER.config_utils.utils import write_to_log
from .SecurityProtocol import decrypt_rsa, decrypt_fernet

class Agent(IntFlag):
    Server = 0b0  # 0 (binary 0)
    Client = 0b1  # 1 (binary 1)

class MsgType(IntFlag):
    Regular = 0b0 << 1  # 0 (binary 00)
    Key     = 0b1 << 1  # 2 (binary 10)

class EncryptionKey(IntFlag):
    Fernet = 0b0 << 2  # 000 (binary 0)
    RSA    = 0b1 << 2 # 100 (binary 4)

class DumpType(IntFlag):
    Regular = 0b0  << 3 # 0000 (binary 0)
    Short   = 0b1  << 3 # 1000 (binary 8)


def type_flags(value: int) -> IntFlag:
    """Types a 4-bit integer back into Sender, MsgType,  EncryptionKey and DumpType."""
    sender = Agent(value & 0b1)       # Extract first 1 bit (Sender)
    msg_type = MsgType(value & 0b10)  # Extract next bit (MsgType)
    key = EncryptionKey(value & 0b100)  # Extract next bit (EncryptionKey)
    dump = DumpType(value & 0b1000)     # Extract next bit (DumpType)
    return sender | msg_type | key | dump


@dataclass
class SessionToken:
    session_code: str = ""
    device_fingerprint: str = ""
    secret: str = ""

    def dump(self) -> str:
        """Serialize the session token into a delimited string."""
        return f"{self.session_code}{SESSION_TOKEN_DELIMITER}{self.device_fingerprint}{SESSION_TOKEN_DELIMITER}{self.secret}"
    
    @staticmethod
    def load(token_str: str) -> "SessionToken":
        """Deserialize a delimited string into a SessionToken object."""
        try:
            parts = token_str.split(SESSION_TOKEN_DELIMITER)
            if len(parts) != 3:
                raise ValueError("Token format invalid.")
            return SessionToken(*parts)
        except Exception as e:
            write_to_log(f"[PACKET_PROTOCOL] Failed to load session token: {e}")
            return None


@dataclass
class Packet:
    packet_type: IntFlag = Agent.Client
    header: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize packet metadata, such as a unique packet ID."""
        self.header.setdefault("packet_id", f"{uuid.uuid4().hex}")

    def setup_body(self, msg: str, args: dict = {}, session_token: SessionToken = None):
        """Configure the packet body and optionally attach a session token."""
        self.body = {"msg": msg, "args": args}
        if session_token:
            self.header["session_token"] = session_token

    def mod_header(self, key: str, val):
        """Adds or modifies a key-value pair in the header dict."""
        try:
            self.header[key] = val
        except Exception as e:
            write_to_log(f"[PACKET_PROTOCOL] Mod header error: {e}")
            return Packet()
        
    def mod_body(self, key: str, val):
        """Adds or modifies a key-value pair in the body dict."""
        try:
            self.body[key] = val
        except Exception as e:
            write_to_log(f"[PACKET_PROTOCOL] Mod body error: {e}")
            return Packet()

    @staticmethod
    def create(msg: str, packet_type: IntFlag = Agent.Client, args: dict = {}, session_token: SessionToken = None):
        p = Packet(packet_type)
        p.setup_body(msg=msg, args=args, session_token=session_token)
        return p

    def dump(self) -> str:
        """Serialize the packet into a string for encryption/transmission."""
        serial_header = self.header.copy()
        if "session_token" in serial_header:
            token = serial_header["session_token"]
            if isinstance(token, SessionToken):
                serial_header["session_token"] = token.dump()
        header_str = json.dumps(serial_header)
        body_str = json.dumps(self.body)
        return header_str + DELIMITER.decode(FORMAT) + body_str
    
    def short_dump(self):
        """For key exchanges."""
        return json.dumps(self.header["packet_id"]) + DELIMITER.decode(FORMAT) + json.dumps(self.body["msg"])

    @staticmethod
    def load(s: str, packet_type: IntFlag = Agent.Client | MsgType.Regular) -> "Packet":
        """Deserialize and reconstruct a packet from its serialized string."""
        try:
            parts = s.split(DELIMITER.decode(FORMAT))
            if len(parts) != 2:
                raise ValueError(f"Malformed packet string - {s}")
            header = json.loads(parts[0])
            body = json.loads(parts[1])

            packet = Packet(packet_type=packet_type)
            if "session_token" in header:
                header["session_token"] = SessionToken.load(header["session_token"])
            packet.header = header
            packet.body = body
            return packet
        except Exception as e:
            write_to_log(f"[PACKET_PROTOCOL] Packet load error: {e}")
            return Packet()
        
    @staticmethod
    def short_load(s: str, packet_type: IntFlag = Agent.Client | MsgType.Key):
        """Deserialize and reconstruct a key packet from its short serialized string."""
        try:
            parts = s.split(DELIMITER.decode(FORMAT))
            if len(parts) != 2:
                raise ValueError(f"Malformed packet string - {s}")
            header = {"packet_id": json.loads(parts[0])}
            body = {"msg": json.loads(parts[1]), "args": {}}
            packet = Packet(packet_type=packet_type)
            packet.header = header
            packet.body = body
            return packet
        except Exception as e:
            write_to_log(f"[PACKET_PROTOCOL] Packet load error: {e}")
            return Packet()



class PacketHandler:
    def __init__(self, type: Agent, rsa_key, fernet_key):
        """Initialize the packet handler with encryption keys."""
        self.type = type
        self.rsa_key = rsa_key
        self.fernet_key = fernet_key

    def change_key(self, key):
        """Update the current Fernet key."""
        self.fernet_key = key

    def parse(self, msg: bytes) -> tuple[Packet, str]:
        """Decrypt and parse an incoming message, determining packet type and contents."""
        try:
            enc_type = msg[:4].decode(FORMAT)
            if not enc_type.isdigit():
                return None, "Invalid packet type prefix."
            msg_type = type_flags(int(enc_type, 2))

            if msg_type & EncryptionKey.RSA:
                if not self.rsa_key:
                    return None, "RSA key is missing."
                packet_str = decrypt_rsa(self.rsa_key, msg[4:])
                if msg_type & DumpType.Short:
                    packet = Packet.short_load(packet_str.decode(FORMAT), msg_type)
                else:
                    packet = Packet.load(packet_str.decode(FORMAT), msg_type)
                if packet.packet_type & MsgType.Key:
                    self.change_key(packet.body["msg"])
                    return Packet.create(""), "Key updated successfully."
                return packet, "Packet parsed successfully."

            else:
                if not self.fernet_key:
                    return None, "Fernet key is missing."
                packet_str = decrypt_fernet(self.fernet_key, msg[4:])
                if msg_type & DumpType.Short:
                    packet = Packet.short_load(packet_str.decode(FORMAT), msg_type)
                else:
                    packet = Packet.load(packet_str.decode(FORMAT), msg_type)
                if packet.packet_type & MsgType.Key:
                    self.change_key(packet.body["msg"])
                    return Packet.create(""), "Key updated successfully."
                if not packet.packet_type & self.type:
                    return packet, "Packet parsed successfully."
                return None, "Packet rejected: invalid agent type."

        except Exception as e:
            write_to_log(f"[PACKET_HANDLER] Failed to parse packet: {e}")
            return None, "Exception during parsing."


if __name__=="__main__":
    pass

