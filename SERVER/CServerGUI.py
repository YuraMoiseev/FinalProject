# Libraries
import threading
from PyQt5 import uic

# Local
from CServerBL import CServerBL
from GUI.PyQtExtensions import *
from MusicalAnalysis.MusicalAnalysis import validate_url, to_wav, AudioExtractor, AudioSeparator
from Protocols.RequestProtocol import *
from config_utils.utils import is_file_present

class CHostGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title_label = None
        self.host_label = None
        self.port_label = None

        self.host_entry = None
        self.port_entry = None

        self.run_button = None

        self.create_connect_wnd()

        self.server = None

    def create_connect_wnd(self):
        uic.loadUi('GUI/UIs/HostWindowGUI.ui', self)
        self.setFixedSize(400, 400)
        self.title_label = self.findChild(QLabel, "LabelTitle")
        self.host_label = self.findChild(QLabel, "LabelHost")
        self.port_label = self.findChild(QLabel, "LabelPort")

        self.host_entry = self.findChild(QLineEdit, "LineEditHost")
        self.host_entry.setText(str(SERVER_HOST))
        self.host_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.port_entry = self.findChild(QLineEdit, "LineEditPort")
        self.port_entry.setText(str(PORT))
        self.port_entry.setStyleSheet(ENTRY_STYLE_SHEET)

        self.run_button = self.findChild(QPushButton, "ButtonRun")
        self.run_button.setStyleSheet(BUTTON_STYLE_SHEET)
        self.run_button.clicked.connect(self.on_click_connect)
        self.show()

    def on_click_connect(self):
        self.server = CServerGUI(host=self.host_entry.text(), port=int(self.port_entry.text()), parent_wnd=self)
        self.hide()


class CServerGUI(CServerBL, QMainWindow):
    def __init__(self, host, port, parent_wnd=None):
        CServerBL.__init__(self, host, port)
        QMainWindow.__init__(self)

        self._parent_wnd = parent_wnd

        self.welcome_label = None
        self.button_add_song_wnd = None
        self.button_requests_wnd = None
        self.button_stop = None
        self.button_users_wnd = None
        self.request_wnd = None
        self.users_wnd = None

        self.create_homepage_ui()
        self._server_thread = threading.Thread(target=self.start_server)
        self._server_thread.start()

    def on_click_stop(self):
        self.stop_server()
        self._parent_wnd.show()
        self.close()

    def closeEvent(self, event):
        self.stop_server()
        event.accept()

    def create_homepage_ui(self):
        uic.loadUi("GUI/UIs/ServerMainPageGUI.ui", self)
        self.setFixedSize(700, 475)

        self.welcome_label = self.findChild(QLabel, "LabelTitle")
        self.button_add_song_wnd = self.findChild(QPushButton, "ButtonAddSongWnd")
        self.button_add_song_wnd.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_add_song_wnd.setFixedSize(200, 50)
        self.button_requests_wnd = self.findChild(QPushButton, "ButtonRequestWnd")
        self.button_requests_wnd.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_requests_wnd.setFixedSize(200, 50)
        self.button_users_wnd = self.findChild(QPushButton, "ButtonUsersWnd")
        self.button_users_wnd.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_users_wnd.setFixedSize(200, 50)
        self.button_stop = self.findChild(QPushButton, "ButtonStop")
        self.button_stop.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_add_song_wnd.clicked.connect(self.on_click_add_song_wnd)
        self.button_requests_wnd.clicked.connect(self.on_click_requests_wnd)
        self.button_users_wnd.clicked.connect(self.on_click_users_wnd)
        self.button_stop.clicked.connect(self.on_click_stop)

        self.show()

    def on_click_add_song_wnd(self):
        pass

    def on_click_requests_wnd(self):
        self.request_wnd = CRequestsGUI(parent_wnd=self)
        self.hide()

    def on_click_users_wnd(self):
        self.users_wnd = CUsersTableGUI(parent_wnd=self)
        self.hide()


# Will be done...
class CAddSongGUI(QMainWindow):
    def __init__(self, parent_wnd=None):
        super().__init__()

        self.label_login = None

        self.login_entry = None

        self.button_back = None
        self.button_register = None
        self.button_login = None
        self.button_forgot_pw = None

        self._parent_wnd = parent_wnd

        self.create_main_ui()

    def create_main_ui(self):
        uic.loadUi("GUI/UIs/LoginGUI.ui", self)
        self.setFixedSize(700, 700)

        self.label_login = self.findChild(QLabel, "LabelLogin")

        self.button_login = self.findChild(QPushButton, "ButtonLogin")
        self.button_forgot_pw = self.findChild(QPushButton, "ButtonForgotPW")
        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_login.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_forgot_pw.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_login.clicked.connect(self.on_click_login)
        self.button_forgot_pw.clicked.connect(self.on_click_forgot_pw)
        self.button_back.clicked.connect(self.back_to_home)

        self.show()


class CUsersTableGUI(QMainWindow):
    def __init__(self, parent_wnd=None):
        super().__init__()

        self.label_title = None

        self.users_table = None

        self.button_back = None

        self._parent_wnd = parent_wnd

        self.create_main_ui()

    def create_main_ui(self):
        uic.loadUi("GUI/UIs/AdminUsers.ui", self)
        self.setFixedSize(1000, 800)

        self.label_title = self.findChild(QLabel, "LabelTitle")

        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.set_up_request_table_widget()

        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_back.clicked.connect(self.on_click_back)

        self.show()

    def set_up_request_table_widget(self):
        # Find the QTableWidget
        original_label = self.findChild(QTableWidget, "TableUsers")

        # Remove the original label from the layout
        layout = original_label.parent().layout()
        layout.removeWidget(original_label)

        # Optionally, delete the original QTableWidget to clean up
        original_label.deleteLater()

        # Create an instance of the custom QRequestsTable
        headers_with_callbacks = USERS_COLUMNS
        headers_with_callbacks["Admin"] = self.client_status
        self.users_table = QRequestsTable(headers_with_callbacks, fetch_users)

        # Add the custom label to the layout
        layout.addWidget(self.users_table)

        # Update the layout to reflect changes
        layout.update()

    def client_status(self, x, y):
        client_state = literal_bool(self.users_table.item(x, y))
        client_id = self.users_table.item(x, 0)
        toggle_client_status(client_id, not client_state)
        self.users_table.setItemValue(x, y, not client_state)

    def on_click_back(self):
        self._parent_wnd.show()
        self.close()


class CRequestsGUI(QMainWindow):
    def __init__(self, parent_wnd=None):
        super().__init__()

        self.label_title = None

        self.request_table = None

        self.button_back = None

        self._parent_wnd = parent_wnd

        self.update_request_wnd = None

        self.create_main_ui()

    def create_main_ui(self):
        uic.loadUi("GUI/UIs/AdminRequests.ui", self)
        self.setFixedSize(1200, 800)

        self.label_title = self.findChild(QLabel, "LabelTitle")

        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.set_up_request_table_widget()

        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_back.clicked.connect(self.on_click_back)

        self.show()

    def set_up_request_table_widget(self):
        # Find the QTableWidget
        original_label = self.findChild(QTableWidget, "TableRequest")

        # Remove the original label from the layout
        layout = original_label.parent().layout()
        layout.removeWidget(original_label)

        # Optionally, delete the original QTableWidget to clean up
        original_label.deleteLater()

        # Create an instance of the custom QRequestsTable
        headers_with_callbacks = REQUESTS_COLUMNS
        headers_with_callbacks["Id"] = self.update_request
        headers_with_callbacks["File Type"] = self.file_download
        headers_with_callbacks["Reject"] = self.delete_request
        headers_with_callbacks["Accept"] = self.accept_request
        self.request_table = QRequestsTable(headers_with_callbacks, fetch_requests)

        # Add the custom label to the layout
        layout.addWidget(self.request_table)

        # Update the layout to reflect changes
        layout.update()

    def on_click_back(self):
        self._parent_wnd.show()
        self.close()


    def file_download(self, x, y):
        request_id = self.request_table.item(x, 0)
        default_path = f"ServerFiles/Request_file_{request_id}_{int(time.time())}.{self.request_table.item(x, y)}"
        file_path, _ = QFileDialog.getSaveFileName(self,'Save File', default_path, 'All Files (*)')
        extract_file("Requests", file_path, request_id, "midi_audio_file", "file_type")


    def delete_request(self, x, _):
        request_id = self.request_table.item(x, 0)
        delete_request(request_id)
        self.request_table.removeRow(x)
        self.request_table.offset -= 1


    def accept_request(self, x, _):
        request_id = self.request_table.item(x, 0)
        file_type = self.request_table.item(x, 5)
        link = self.request_table.item(x, 3)
        if file_type == "mp3":
            path_mp3 = f"ServerFiles/Request_file_{request_id}_{int(time.time())}.mp3"
            extract_file("Requests", path_mp3, request_id, "midi_audio_file", "file_type")
            path_wav = to_wav(path_mp3)
            os.remove(path_mp3)
            # Separate stems
            separator = AudioSeparator(path_wav)
            sep_dir = separator.separate_all()
            os.remove(path_wav)
            # Analyze each stem and save as a whole midi file
            analyzer = AudioAnalyzer()
            files = os.listdir(sep_dir)
            for filename in files:
                analyzer.change_base_file(os.path.join(os.getcwd(), sep_dir, filename))
                analyzer.analyze_smart(filename, 0.05)  # Analyse with best suiting tools for each stem
                os.remove(filename)
            path_mid = analyzer.save_midi(f"Request_file_{request_id}_{int(time.time())}.mid")
            # Save the midi file to the database
            song_name, artist_name, requester = self.request_table.item(x, 1), self.request_table.item(x, 2), self.request_table.item(x, 6)
            add_song(path_mid, song_name, artist_name, requester)
            os.remove(path_mid)
            self.delete_request(x, _)

        if file_type == "wav":
            path_wav = f"ServerFiles/Request_file_{request_id}_{int(time.time())}.wav"
            extract_file("Requests", path_wav, request_id, "midi_audio_file", "file_type")
            # Separate stems
            separator = AudioSeparator(path_wav)
            sep_dir = separator.separate_all()
            os.remove(path_wav)
            # Analyze each stem and save as a whole midi file
            analyzer = AudioAnalyzer()
            for filename in os.listdir(sep_dir):
                analyzer.change_base_file(os.path.join(os.getcwd(), sep_dir, filename))
                analyzer.analyze_smart(filename, 0.05)  # Analyse with best suiting tools for each stem
            path_mid = analyzer.save_midi(f"Request_file_{request_id}_{int(time.time())}.mid")
            # Save the midi file to the database
            song_name, artist_name, requester = self.request_table.item(x, 1), self.request_table.item(x, 2), self.request_table.item(x, 6)
            add_song(path_mid, song_name, artist_name, requester)
            os.remove(path_mid)
            self.delete_request(x, _)
            write_to_log("Song successfully added!")

        elif file_type == "mid":
            path_wav = f"ServerFiles/Request_file_{request_id}_{int(time.time())}.mid"
            song_name, artist_name, requester = self.request_table.item(x, 1), self.request_table.item(x, 2), self.request_table.item(x, 6)
            extract_file("Requests", path_wav, request_id, "midi_audio_file", "file_type")
            add_song(path_wav, song_name, artist_name, requester)
            os.remove(path_wav)
            self.delete_request(x, _)
            write_to_log("Song successfully added!")

        elif validate_url(link):
            extractor = AudioExtractor()
            path_wav = extractor.download_audio(link)
            if path_wav is not None:
                # Separate stems
                separator = AudioSeparator(path_wav)
                sep_dir = separator.separate_all()
                # os.remove(path_wav)
                # Analyze each stem and save as a whole midi file
                analyzer = AudioAnalyzer()
                for filename in os.listdir(sep_dir):
                    analyzer.change_base_file(os.path.join(os.getcwd(), sep_dir, filename))
                    analyzer.analyze_smart(filename, 0.05) # Analyse with best suiting tools for each stem
                path_mid = analyzer.save_midi(f"Request_file_{request_id}_{int(time.time())}.mid")
                # Save the midi file to the database
                song_name, artist_name, requester = self.request_table.item(x, 1), self.request_table.item(x, 2), self.request_table.item(x, 6)
                add_song(path_mid, song_name, artist_name, requester)
                os.remove(path_mid)
                self.delete_request(x, _)
                write_to_log("Song successfully added!")
            else:
                write_to_log(f"Invalid YouTube link, could not accept request {request_id}")

        else:
            write_to_log(f"Invalid file type, could not accept request {request_id}")


    def update_request(self, x, _):
        data = self.request_table.getRowData(x)
        self.update_request_wnd = RequestWindow(x, data, self)


class RequestWindow(QMainWindow):
    def __init__(self, row: int, data: list, parent_wnd=None):
        QMainWindow.__init__(self)
        self._parent_wnd = parent_wnd

        self.label_title = None
        self.label_name = None
        self.label_artist = None
        self.label_link = None
        self.label_description = None
        self.label_file = None
        self.label_request_fail = None

        self.entries_data = data
        self.row = row
        self.name_entry = None
        self.artist_entry = None
        self.link_entry = None
        self.description_entry = None
        self.file_drop = None
        self.entries = []

        self.button_save_request = None
        self.button_back = None
        self.create_main_ui()

    def create_main_ui(self):
        uic.loadUi("GUI/UIs/RequestClientWndGUI.ui", self)
        self.setFixedSize(900, 700)

        self.label_title = self.findChild(QLabel, "LabelTitle")
        self.label_request_fail = self.findChild(QLabel, "SuccessFailLabel")
        self.label_request_fail.hide()

        self.label_name = self.findChild(QLabel, "LabelName")
        self.name_entry = self.findChild(QLineEdit, "LineEditName")
        self.name_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.name_entry.setText(self.entries_data[1])

        self.label_artist = self.findChild(QLabel, "LabelArtist")
        self.artist_entry = self.findChild(QLineEdit, "LineEditArtist")
        self.artist_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.artist_entry.setText(self.entries_data[2])


        self.label_link = self.findChild(QLabel, "LabelLink")
        self.link_entry = self.findChild(QLineEdit, "LineEditLink")
        self.link_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.link_entry.setText(self.entries_data[3])

        self.label_description = self.findChild(QLabel, "LabelDescription")
        self.description_entry = self.findChild(QLineEdit, "LineEditDescription")
        self.description_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.description_entry.setText(self.entries_data[4])


        self.entries.append(self.name_entry)
        self.entries.append(self.artist_entry)
        self.entries.append(self.link_entry)
        self.entries.append(self.description_entry)

        self.label_file = self.findChild(QLabel, "LabelFile")
        self.set_up_file_drop_widget()
        self.file_drop.chosen_file_path = "_"

        self.button_save_request = self.findChild(QPushButton, "ButtonRequest")
        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_save_request.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_save_request.clicked.connect(self.on_click_save_request)
        self.button_back.clicked.connect(self.back_to_home)

        self.show()

    def set_up_file_drop_widget(self):
        """
        A function that sets up the QFileDropWidget
        Replaces the original auxiliary widget from ui
        """
        # Find the QLabel
        original_label = self.findChild(QLabel, "FileDrop")

        # Remove the original label from the layout
        layout = original_label.parent().layout()
        layout.removeWidget(original_label)

        # Optionally, delete the original QLabel to clean up
        original_label.deleteLater()

        # Create an instance of the custom FileDropLabel
        self.file_drop = QFileDropWidget(self)

        # Add the custom label to the layout
        layout.addWidget(self.file_drop)

        # Update the layout to reflect changes
        layout.update()

    def back_to_home(self):
        self._parent_wnd.show()
        self.close()

    def on_click_save_request(self):
        file_type = ""
        if self.file_drop.chosen_file_path is not None and is_file_present(self.file_drop.chosen_file_path):
            file_type = self.file_drop.chosen_file_path.split(".")[-1]

        data = { "id": self.entries_data[0],
                "name": self.name_entry.text(), "artist": self.artist_entry.text(),
                "link": self.link_entry.text(), "description": self.description_entry.text(),
                "file": file_type
                }
        result = update_request(data, self.file_drop.chosen_file_path)
        if result == "Success":
            updated_data = list(data.values())
            self._parent_wnd.request_table.updateRowData(self.row, updated_data)
            self.close()

        if type(result) == bool:
            if result:
                result = "Successfully sent"
            else:
                result = "Error"
        self.label_request_fail.setText(str(result))
        self.label_request_fail.show()
        self.file_drop.chosen_file_path = "_"

    def closeEvent(self, event):
        self._parent_wnd.children_requests_window = None
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    server = CHostGUI()
    app.exec_()





