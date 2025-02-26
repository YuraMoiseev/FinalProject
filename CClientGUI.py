import threading
from Protocol import *
from CClientBL import CClientBL
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup, QPoint
from PyQt5 import uic
from PyQtExtensions import QFileDropWidget, QPopUpWidget
import ast


class CConnectGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title_label = None
        self.host_label = None
        self.port_label = None

        self.host_entry = None
        self.port_entry = None

        self.connect_button = None

        self.create_connect_wnd()

        self.client = None

    def create_connect_wnd(self):
        uic.loadUi('GUI/UIs/ConnectWindowGUI.ui', self)
        self.setFixedSize(400, 400)
        self.title_label = self.findChild(QLabel, "LabelTitle")
        self.host_label = self.findChild(QLabel, "LabelHost")
        self.port_label = self.findChild(QLabel, "LabelPort")

        self.host_entry = self.findChild(QLineEdit, "LineEditHost")
        self.host_entry.setText(str(CLIENT_HOST))
        self.host_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.port_entry = self.findChild(QLineEdit, "LineEditPort")
        self.port_entry.setText(str(PORT))
        self.port_entry.setStyleSheet(ENTRY_STYLE_SHEET)

        self.connect_button = self.findChild(QPushButton, "ButtonConnect")
        self.connect_button.setStyleSheet(BUTTON_STYLE_SHEET)
        self.connect_button.clicked.connect(self.on_click_connect)
        self.show()

    def on_click_connect(self):
        self.client = CClientGUI(host=self.host_entry.text(), port=int(self.port_entry.text()), parent_wnd=self)
        self.hide()


class CClientGUI(CClientBL, QMainWindow):
    def __init__(self, host, port, parent_wnd=None):
        CClientBL.__init__(self, host, port)
        QMainWindow.__init__(self)

        self._parent_wnd = parent_wnd

        self.welcome_label = None
        self.button_reg = None
        self.button_login = None
        self.button_back = None
        self.windows = []

        self.welcome_label_anim = None
        self.buttons_anim = None
        self.window_anim = None
        self.connected = False
        self.update_thread_lock = False
        self.update_thread = None

        self._client_socket = self.connect()
        if self._client_socket is not None:
            self.create_homepage_ui()
            self.connected = True
            self.update_thread = threading.Thread(target=self.update_check)
            # self.update_thread.start()
        else:
            self.create_error_wnd()


    def create_error_wnd(self):
        uic.loadUi('GUI/UIs/ErrorWindowGUI.ui', self)
        self.setFixedSize(600, 400)
        self.button_back = self.findChild(QPushButton, "ButtonBack")
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_back.clicked.connect(self.on_click_back)
        self.show()

    def on_click_back(self):
        self._parent_wnd.show()
        self.close()

    def welcome_label_animation(self):
        try:
            opacity_effect = QGraphicsOpacityEffect(self.welcome_label)
            self.welcome_label.setGraphicsEffect(opacity_effect)
            welcome_label_anim1 = QPropertyAnimation(opacity_effect, b"opacity")
            welcome_label_anim1.setStartValue(0)
            welcome_label_anim1.setEndValue(1)
            welcome_label_anim1.setDuration(2500)

            welcome_label_anim2 = QPropertyAnimation(self.welcome_label, b"pos")
            welcome_label_anim2.setEndValue(QPoint(50, -49))
            welcome_label_anim2.setDuration(500)
            self.welcome_label_anim = QSequentialAnimationGroup(self)
            self.welcome_label_anim.addAnimation(welcome_label_anim1)
            self.welcome_label_anim.addAnimation(welcome_label_anim2)

        except Exception as e:
            write_to_log(f"Exception on animating client GUI - {e}")

    def buttons_animation(self):
        try:
            opacity_effect_reg = QGraphicsOpacityEffect(self.button_reg)
            self.button_reg.setGraphicsEffect(opacity_effect_reg)
            button_reg_anim = QPropertyAnimation(opacity_effect_reg, b"opacity")
            button_reg_anim.setStartValue(0)
            button_reg_anim.setEndValue(1)
            button_reg_anim.setDuration(2500)

            opacity_effect_login = QGraphicsOpacityEffect(self.button_login)
            self.button_login.setGraphicsEffect(opacity_effect_login)
            button_login_anim = QPropertyAnimation(opacity_effect_login, b"opacity")
            button_login_anim.setStartValue(0)
            button_login_anim.setEndValue(1)
            button_login_anim.setDuration(2500)

            self.buttons_anim = QParallelAnimationGroup()
            self.buttons_anim.addAnimation(button_reg_anim)
            self.buttons_anim.addAnimation(button_login_anim)

        except Exception as e:
            write_to_log(f"Exception on animating client GUI - {e}")

    def window_animation(self):

        self.welcome_label_animation()
        self.buttons_animation()

        self.button_reg.hide()
        self.button_login.hide()

        self.window_anim = QSequentialAnimationGroup()
        self.window_anim.addAnimation(self.welcome_label_anim)
        self.window_anim.addAnimation(self.buttons_anim)

        self.welcome_label_anim.finished.connect(self.show_buttons)

        self.window_anim.start()

    def show_buttons(self):
        self.button_reg.show()
        self.button_login.show()

    def create_homepage_ui(self):
        uic.loadUi("GUI/UIs/HomePageGUI.ui", self)
        self.setFixedSize(600, 475)

        self.welcome_label = self.findChild(QLabel, "LabelWelcome")
        self.button_reg = self.findChild(QPushButton, "ButtonRegister")
        self.button_reg.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_reg.setFixedSize(200, 50)
        self.button_login = self.findChild(QPushButton, "ButtonLogin")
        self.button_login.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_login.setFixedSize(200, 50)
        self.button_back = self.findChild(QPushButton, "ButtonBack")
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_reg.clicked.connect(self.on_click_register)
        self.button_login.clicked.connect(self.on_click_login)
        self.button_back.clicked.connect(self.on_click_back)

        self.window_animation()

        self.show()

    def on_click_register(self):

        self.windows.append(CLoginGUI(parent_wnd=self, client_object=self))
        self.hide()
        self.windows[-1].create_register_ui()

    def on_click_login(self):
        # Check the server database for a stored hash of the device to login via an unclose session
        data = {"device_id": self.device_id}
        self.safe_send(f"Login_with_session>{data}")
        result = self.safe_receive()
        if result == LOGIN_SUCCESS:
            self.windows.clear()
            pop_up = QPopUpWidget(POP_UP_LABEL1, POP_UP_LABEL2, self)
            if pop_up.exec_():
                self.windows.append(MainWindow(parent_wnd=self))
                self.hide()
            else:
                self.safe_send(f"Delete_session")
                self.windows.append(CLoginGUI(parent_wnd=self, client_object=self))
                self.hide()
                self.windows[-1].create_login_ui()
        else:
            self.windows.append(CLoginGUI(parent_wnd=self, client_object=self))
            self.hide()
            self.windows[-1].create_login_ui()

    def closeEvent(self, event):
        if not self.connected:
            event.accept()
        else:
            self.safe_send(DISCONNECT_MSG)
            if self.safe_receive() == "Bye!":
                event.accept()
            else:
                event.ignore()

    # constant checks if the client is still connected to the server
    def update_check(self):
        while self.connected and not self.update_thread_lock:
            self.safe_send("Update")
            self.safe_receive()
            time.sleep(1)


    # terminates the workflow in case of an exception arising
    def safe_send(self, data):
        is_sent = self.send_data(data)
        if not is_sent:
            self.forced_termination()
            # return False
        else:
            return True

    # terminates the workflow in case of an exception arising
    def safe_receive(self):
        receive = self.receive_data()
        if any(substring in receive for substring in ERROR_MSGS):
            self.forced_termination()
        else:
            return receive

    # in case the connection is broken and termination is required
    def forced_termination(self):
        self.connected = False
        pop_up = QPopUpWidget("An error occurred in the workflow. The application will be terminated", POP_UP_LABEL2, self, (1, ["OK"]))
        if pop_up.exec_():
            for window in self.windows:
                window.close()
            self.windows.clear()
            self._parent_wnd.client = CClientGUI(self._host, self._port, self._parent_wnd)
            self.close()


class CLoginGUI(QDialog):
    def __init__(self, parent_wnd=None, client_object=None):
        QDialog.__init__(self)

        self._parent_wnd = parent_wnd
        self._client_object = client_object

        self.label_login = None
        self.label_password = None
        self.label_email = None
        self.label_reg_fail = None
        self.label_login_fail = None

        self.login_entry = None
        self.password_entry = None
        self.email_entry = None

        self.button_back = None
        self.button_register = None
        self.button_login = None
        self.button_forgot_pw = None

    def create_login_ui(self):
        uic.loadUi("GUI/UIs/LoginGUI.ui", self)
        self.setFixedSize(700, 700)

        self.label_login_fail = self.findChild(QLabel, "LabelLoginFail")
        self.label_login_fail.setWordWrap(True)
        self.label_login_fail.hide()

        self.label_login = self.findChild(QLabel, "LabelLogin")
        self.login_entry = self.findChild(QLineEdit, "LineEditLogin")
        self.login_entry.setStyleSheet(ENTRY_STYLE_SHEET)

        self.label_password = self.findChild(QLabel, "LabelPassword")
        self.password_entry = self.findChild(QLineEdit, "LineEditPassword")
        self.password_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.password_entry.setEchoMode(QLineEdit.Password)

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

    def create_register_ui(self):
        uic.loadUi("GUI/UIs/RegisterWindowGUI.ui", self)
        self.setFixedSize(700, 700)

        self.label_reg_fail = self.findChild(QLabel, "LabelRegFail")
        self.label_reg_fail.setWordWrap(True)
        self.label_reg_fail.hide()

        self.label_login = self.findChild(QLabel, "LabelLogin")
        self.login_entry = self.findChild(QLineEdit, "LineEditLogin")
        self.login_entry.setStyleSheet(ENTRY_STYLE_SHEET)

        self.label_email = self.findChild(QLabel, "LabelEmail")
        self.email_entry = self.findChild(QLineEdit, "LineEditEmail")
        self.email_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.email_entry.setText("@gmail.com")

        self.label_password = self.findChild(QLabel, "LabelPassword")
        self.password_entry = self.findChild(QLineEdit, "LineEditPassword")
        self.password_entry.setStyleSheet(ENTRY_STYLE_SHEET)
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.button_register = self.findChild(QPushButton, "ButtonRegister")
        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_register.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_register.clicked.connect(self.on_click_register)
        self.button_back.clicked.connect(self.back_to_home)

        self.show()

    def back_to_home(self):
        self._parent_wnd.show()
        self.close()

    def on_click_register(self):
        login = self.login_entry.text()
        password = self.password_entry.text()
        email = self.email_entry.text()
        validity = verify_entry_validity(login, email, password)
        if not validity[0]:
            self.label_reg_fail.show()
            self.label_reg_fail.setText(validity[1])
        else:
            data = {"login": login, "email": email, "password": password}
            self._parent_wnd.safe_send(f"Register>{data}")
            result = self._parent_wnd.safe_receive()
            if result != REG_SUCCESS:
                self.label_reg_fail.show()
                self.label_reg_fail.setText(result)
            else:
                self.back_to_home()

    def on_click_login(self):
        login_text = self.login_entry.text()
        password_text = self.password_entry.text()
        data = {"login": login_text, "password": password_text, "device_id" : self._parent_wnd.device_id}
        self._parent_wnd.safe_send(f"Login_with_data>{data}")
        success = self._parent_wnd.safe_receive()
        if success != LOGIN_SUCCESS:
            self.label_login_fail.setText(success)
            self.label_login_fail.show()
        else:
            self._parent_wnd.windows.clear()
            # main_window = MainWindow(callback_home=back_home,callback_send=send)
            main_window = MainWindow(parent_wnd=self._parent_wnd)
            self._parent_wnd.windows.append(main_window)
            self.hide()
            # main_window.create_main_ui()


    def on_click_forgot_pw(self):
        write_to_log("Pomnit' Nada")


# class ForgotPassword(QDialog):
#     def __init__(self, parent=None):


class MainWindow(QMainWindow):
    def __init__(self, parent_wnd=None):
        QMainWindow.__init__(self)

        self._parent_wnd = parent_wnd

        self.children_record_window = None
        self.children_songs_window = None
        self.children_requests_window = None


        self.label_welcome = None
        self.label_do_next = None

        self.button_trace = None
        self.button_songs = None
        self.button_requests = None
        self.button_back = None

        self.create_main_ui()

    def create_main_ui(self):
        uic.loadUi("GUI/UIs/MainWindowGUI.ui", self)
        self.setFixedSize(800, 500)

        self.label_welcome = self.findChild(QLabel, "LabelWelcome")
        self.label_do_next = self.findChild(QLabel, "LabelDoNext")

        self.button_trace = self.findChild(QPushButton, "ButtonTrace")
        self.button_songs = self.findChild(QPushButton, "ButtonSongs")
        self.button_requests = self.findChild(QPushButton, "ButtonRequests")

        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_trace.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_songs.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_requests.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_back.clicked.connect(self.on_click_back)
        self.button_trace.clicked.connect(self.on_click_trace)
        self.button_songs.clicked.connect(self.on_click_songs)
        self.button_requests.clicked.connect(self.on_click_requests)
        self.show()


    def on_click_trace(self):
        if self.children_record_window is None:
            self.children_record_window = RecordWindow(self, self._parent_wnd)

    def on_click_requests(self):
        if self.children_requests_window is None:
            self.children_requests_window = RequestWindow(self, self._parent_wnd)


    def on_click_songs(self):
        print("Will be done later...")

    def on_click_back(self):
        self._parent_wnd.safe_send("Delete_session")
        result = self._parent_wnd.safe_receive()
        write_to_log(result)
        self._parent_wnd.show()
        self.hide()

    def closeEvent(self, event):
        if not self._parent_wnd.connected:
            event.accept()
        else:
            self._parent_wnd.safe_send(DISCONNECT_MSG)
            if self._parent_wnd.safe_receive() == "Bye!":
                event.accept()
            else:
                event.ignore()


class RecordWindow(QMainWindow):
    def __init__(self, parent_wnd=None, client_object=None):
        QMainWindow.__init__(self)

        self._parent_wnd = parent_wnd
        self._client_object = client_object

        self.label_record = None

        self.button_record = None
        self.button_back = None
        self.combo_box_devices = None
        self.create_main_ui()

    def create_main_ui(self):
        uic.loadUi("GUI/UIs/RecordWndGUI.ui", self)
        self.setFixedSize(500, 650)

        self.label_record = self.findChild(QLabel, "LabelRecord")

        self.button_back = self.findChild(QPushButton, "ButtonBack")
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_record = self.findChild(QPushButton, "ButtonRecord")
        self.button_record.setStyleSheet("""
        QPushButton {
                    border: 2px solid #00ff00;
                    border-image: url('GUI/Images/microphone_img_final.png');
                    }
        QPushButton:hover {
                    border: 2px solid #00ff00;
                    border-image: url('GUI/Images/microphone_img_final_hover.png');
                    }
        QPushButton:pressed {
                    border: 2px solid #00ff00;
                    border-image: url('GUI/Images/microphone_img_final_pressed.png');
                    }
                """)
        self.button_record.setFixedSize(300, 300)
        self.combo_box_devices = self.findChild(QComboBox, "ComboBoxAudioDevices")
        self.setup_combo_box()
        self.button_back.clicked.connect(self.on_click_back)
        self.button_record.clicked.connect(self.on_click_record)
        self.show()

    def setup_combo_box(self):
        devices = self._client_object.get_audio_devices()
        for i in devices:
            self.combo_box_devices.addItem(i)
        self.combo_box_devices.currentIndexChanged.connect(self.select_audio_device)

    def select_audio_device(self):
        self._client_object.select_audio_device(self.combo_box_devices.currentText())

    def _record(self):
        self._client_object.update_thread_lock = True
        self._client_object.record_wav("recording.wav")
        self.label_record.setText("Recording done. Sending data to the server...")
        self._client_object.safe_send(SEARCH_SONG_REQUEST)
        # result = self._client_object.safe_receive()
        # print(result)
        # if result == SEND_FILE_APPROVE:
        self._client_object.send_file("recording.wav")
        write_to_log(1)
        result = ast.literal_eval(self._client_object.safe_receive())
        write_to_log(2)
        displayed_text = "Found songs \n"
        for i in result:
            displayed_text += f"{i[1]} by {i[2]} is {i[0]}% similar to your recording"
        write_to_log(3)
        pop_up = QPopUpWidget(displayed_text, POP_UP_LABEL2, self, (1, ["OK"]))
        if pop_up.exec_():
            self.close()
        write_to_log(4)
        self._client_object.update_thread_lock = False
        try:
            os.remove("recording.wav")
            write_to_log(f"File 'recording.wav' has been deleted successfully.")
        except Exception as e:
            write_to_log(f"An error occurred: {e}")
        if not self._client_object.is_recording:
            return

        self._client_object.cond()
        # time.sleep(3)
        # self.label_record.setText("Record")

    def on_click_record(self):
        if not self._client_object.is_recording:
            self.label_record.setText("Recording...")
            self._client_object.cond()
            recording = threading.Thread(target=self._record)
            recording.start()

        else:
            self.label_record.setText("Record")
            self._client_object.cond()

    def on_click_back(self):
        self._parent_wnd.show()
        self.close()

    def closeEvent(self, event):
        self._parent_wnd.children_record_window = None
        event.accept()


class RequestWindow(QMainWindow):
    def __init__(self, parent_wnd=None, client_object=None):
        QMainWindow.__init__(self)
        self._parent_wnd = parent_wnd
        self._client_object = client_object

        self.label_title = None
        self.label_name = None
        self.label_artist = None
        self.label_link = None
        self.label_description = None
        self.label_file = None
        self.label_request_fail = None

        self.name_entry = None
        self.artist_entry = None
        self.link_entry = None
        self.description_entry = None
        self.file_drop = None
        self.entries = []

        self.button_send_request = None
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

        self.label_artist = self.findChild(QLabel, "LabelArtist")
        self.artist_entry = self.findChild(QLineEdit, "LineEditArtist")
        self.artist_entry.setStyleSheet(ENTRY_STYLE_SHEET)

        self.label_link = self.findChild(QLabel, "LabelLink")
        self.link_entry = self.findChild(QLineEdit, "LineEditLink")
        self.link_entry.setStyleSheet(ENTRY_STYLE_SHEET)

        self.label_description = self.findChild(QLabel, "LabelDescription")
        self.description_entry = self.findChild(QLineEdit, "LineEditDescription")
        self.description_entry.setStyleSheet(ENTRY_STYLE_SHEET)

        self.entries.append(self.name_entry)
        self.entries.append(self.artist_entry)
        self.entries.append(self.link_entry)
        self.entries.append(self.description_entry)

        self.label_file = self.findChild(QLabel, "LabelFile")
        self.set_up_file_drop_widget()

        self.button_send_request = self.findChild(QPushButton, "ButtonRequest")
        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_send_request.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_send_request.clicked.connect(self.on_click_send_request)
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


    def on_click_send_request(self):
        if self.name_entry.text() != "":
            file_type = ""
            if self.file_drop.chosen_file_path is not None and is_file_present(self.file_drop.chosen_file_path):
                file_type = self.file_drop.chosen_file_path.split(".")[-1]

            data = {
                "name": self.name_entry.text(), "artist": self.artist_entry.text(),
                "link": self.link_entry.text(), "description": self.description_entry.text(),
                "file": file_type
            }
            # data = {key:("" if value is None else value) for key, value in data.items()}
            self._client_object.safe_send(f"Request>{data}")
            write_to_log(f"Request>{data}")
            if self.file_drop.chosen_file_path is not None:
                result = self._client_object.send_file(self.file_drop.chosen_file_path)
            else:
                result = self._client_object.safe_receive()
            if type(result) == bool:
                if result:
                    result = "Successfully sent"
                else:
                    result = "Error"
            self.label_request_fail.setText(str(result))
            self.label_request_fail.show()
            for entry in self.entries:
                entry.setText("")
            self.file_drop.handle_delete()

    def closeEvent(self, event):
        self._parent_wnd.children_requests_window = None
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    Client = CConnectGUI()
    # client = RequestWindow()
    app.exec_()
