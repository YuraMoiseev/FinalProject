# Libraries
import time
import os
import json

# Local
from SERVER.MusicalAnalysis.MusicalAnalysis import AudioAnalyzer, MidiAnalyzer
import SERVER.Protocols.DBProtocol as DBProtocol
from SERVER.Protocols.Protocol import receive_file
from SERVER.Protocols.PacketProtocol import Packet, Agent, MsgType
from SERVER.Protocols.SecurityProtocol import generate_fernet_key
from SERVER.config_utils.utils import write_to_log
from SERVER.config_utils.config import SEARCH_SONG_REQUEST, SEND_FILE_SUCCESS, SEND_FILE_FAIL, DISCONNECT_MSG, FORMAT


def check_cmd(cmd):
    if type(cmd) == bytes:
        cmd = cmd.decode(FORMAT)
    if cmd in REQUESTS_1:
        return 1
    if cmd in REQUESTS_2:
        return 2
    if cmd in LOGIN_REQUESTS:
        return 3
    return 0


def create_response_and_execute_reaction(packet: Packet, session_id, client_handler) -> Packet: # Session id is kept in the client handler on the server side and thus cannot be obtained from client's message
    """Create and a valid protocol message, will be sent by server, with length field"""
    def handle_request_with_file():
        file_name = None
        file_type = None
        if packet.body["args"]["file"] != "":
            write_to_log("[SERVER_BL] receiving file...")
            # new file name is defined by how many files have been created
            is_recv, file_name = receive_file(client_handler.client_socket, packet.body["args"]["file"], client_handler.packet_handler)
            file_type = file_name.split(".")[-1]
            if not is_recv:
                write_to_log("Error - file count not be transferred")

        result = DBProtocol.add_request(packet.body["args"], session_id, file_name, file_type)
        if packet.body["args"]["file"] != "":
            os.remove(file_name)
        return result

    def handle_song_search():
        #try:
        write_to_log("[SERVER_BL] receiving file...")
        is_recv, file_name = receive_file(client_handler.client_socket, "wav", client_handler.packet_handler)
        if not is_recv:
            write_to_log("Error - file count not be transferred")
            return
        print("file:" + file_name)
        songs = DBProtocol.fetch_songs()
        # write_to_log(f"[PROTOCOL] fetched songs: {list(songs.keys())}")
        audio_analyzer = AudioAnalyzer(file_name)
        audio_analyzer.analyze_full()
        # write_to_log(7)
        midi_analyzer = MidiAnalyzer.load_from_audio_analyzer(audio_analyzer)
        # write_to_log(8)
        time1 = time.time()
        # res_best_python = midi_analyzer.compare_to_db(songs)
        time2 = time.time()
        res_best_rust = midi_analyzer.compare_to_db_rust(songs)
        time3 = time.time()
        write_to_log(f"[PROTOCOL] Python runtime:{time2-time1}  Rust runtime:{time3-time2}")
        # write_to_log(9)
        os.remove(file_name)
        # write_to_log(10)
        # write_to_log(f"[PROTOCOL] 20 best songs are: {res_best}")
        return json.dumps(res_best_rust)
        # except Exception as e:
        #     write_to_log(f"Exception on handling song search: {e}")
        #     return "Error"

    packet_id, cmd, args = packet.header["packet_id"], packet.body["msg"], packet.body["args"]
    resp_packet = Packet.create(packet_type = Agent.Server | MsgType.Regular, msg="", args={})
    resp_packet.mod_body("id", packet_id)
    if "session_token" in packet.header:
        session_token = packet.header["session_token"]
    else:
        session_token = ""
    if cmd is None:
        resp_packet.mod_body("msg", "Invalid message")
        return resp_packet
    if type(packet) != Packet:
        resp_packet.mod_body("msg", "Invalid packet type")
        return resp_packet
    if cmd in SESSION_REQUESTS:
        is_cmd_allowed = DBProtocol.handle_session_limit(session_token.session_code)
        if not is_cmd_allowed:
            resp_packet.mod_body("msg", "Invalid session")
            resp_packet.mod_body("session", "")
            return resp_packet
    if check_cmd(cmd) == 1:
        resp_packet.mod_body("msg", REQUESTS_1[cmd])
    elif cmd == "Rotate_key":
        f_key = generate_fernet_key().decode(FORMAT)
        client_handler.packet_handler.change_key(f_key)
        resp_packet.mod_body("msg", f_key)
    elif cmd == "Register":
        resp_packet.mod_body("msg", DBProtocol.register_client(args))
    elif cmd == "Request_password_reset":
        res = DBProtocol.request_password_reset(args.get("email", ""))
        resp_packet.mod_body("msg", res)
    elif cmd == "Verify_password_reset_code":
        res = DBProtocol.verify_reset_code(args.get("email", ""), args.get("code", ""))
        resp_packet.mod_body("msg", res)
    elif cmd == "Confirm_password_reset":
        res = DBProtocol.confirm_password_reset(args.get("email", ""), args.get("code", ""), args.get("new_password", ""))
        resp_packet.mod_body("msg", res)
    elif cmd == "Login_with_data":
        response, session_code, client_handler.session = DBProtocol.login_with_data(args)
        resp_packet.mod_body("msg", response)
        resp_packet.mod_body("session", session_code)
    elif cmd == "Login_with_session":
        response, session_code, client_handler.session = DBProtocol.login_with_old_session(session_token.session_code)
        resp_packet.mod_body("msg", response)
        resp_packet.mod_body("session", session_code)
    elif cmd == "Request":
        resp_packet.mod_body("msg", handle_request_with_file())
    elif cmd == "Delete_session":
        resp_packet.mod_body("msg", DBProtocol.delete_session(session_id))
    elif cmd == "Songs":
        song_names = DBProtocol.fetch_song_names(args.get("offset", 0))
        resp_packet.mod_body("msg", "Here are the songs:")
        resp_packet.mod_body("args", song_names)
    elif cmd == SEARCH_SONG_REQUEST:
        resp_packet.mod_body("msg", handle_song_search())
    else:
        resp_packet.mod_body("msg", "Error")
    if resp_packet.body["msg"] == "Bye!":
        client_handler.connected = False
        DBProtocol.toggle_session_state(session_id, False)
    return resp_packet


REQUESTS_1 = {"Hello": "Hello!",
              SEND_FILE_SUCCESS: SEND_FILE_SUCCESS, SEND_FILE_FAIL: SEND_FILE_FAIL, DISCONNECT_MSG: "Bye!", "Update": "All Good"}

REQUESTS_2 = {"Register", "Request", "Delete_session", SEARCH_SONG_REQUEST, "Rotate_key", "Verify_password_reset_code", "Request_password_reset", "Confirm_password_reset", "Songs"}


LOGIN_REQUESTS = {"Login_with_session", "Login_with_data"}

SESSION_REQUESTS = {"Request", "Login_with_session", "Delete_session", SEARCH_SONG_REQUEST, "Upd", "Songs"}