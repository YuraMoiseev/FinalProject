import threading
import time

from protocol import *
from CClientBL import CClientBL
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QMainWindow, QLabel, QLineEdit, QGraphicsOpacityEffect, \
    QWidget
from PyQt5.QtCore import QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup, QPoint
from PyQt5 import uic

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
        uic.loadUi('ConnectWindowGUI.ui', self)
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

        self._client_socket = self.connect()
        if self._client_socket is not None:
            self.create_homepage_ui()
        else:
            self.create_error_wnd()


    def create_error_wnd(self):
        uic.loadUi('ErrorWindowGUI.ui', self)
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
        uic.loadUi("HomePageGUI.ui", self)
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

        obj = CLoginGUI(parent_wnd=self)
        self.windows.append(obj)
        self.hide()
        obj.create_register_ui()

    def on_click_login(self):

        obj = CLoginGUI(parent_wnd=self)
        self.windows.append(obj)
        self.hide()
        obj.create_login_ui()


class CLoginGUI(QDialog):
    def __init__(self, parent_wnd=None):
        QDialog.__init__(self)

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

        self._parent_wnd = parent_wnd

    def create_login_ui(self):
        uic.loadUi("LoginGUI.ui", self)
        self.setFixedSize(700, 700)

        self.label_login_fail = self.findChild(QLabel, "LabelLoginFail")
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
        uic.loadUi("RegisterWindowGUI.ui", self)
        self.setFixedSize(700, 700)

        self.label_reg_fail = self.findChild(QLabel, "LabelRegFail")
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
            self._parent_wnd.send_data(f"Register>{data}")
            result = self._parent_wnd.receive_data()
            if result != REG_SUCCESS:
                self.label_reg_fail.show()
                self.label_reg_fail.setText(result)
            else:
                self.back_to_home()

    def on_click_login(self):
        login_text = self.login_entry.text()
        password_text = self.password_entry.text()
        data = {"login": login_text, "password": password_text}
        self._parent_wnd.send_data(f"Login>{data}")
        success = self._parent_wnd.receive_data()
        if success != LOGIN_SUCCESS:
            self.label_login_fail.setText(success)
            self.label_login_fail.show()
        else:
            self._parent_wnd.windows.clear()
            # main_window = MainWindow(callback_home=back_home,callback_send=send)
            main_window = RecordWindow(parent_wnd=self._parent_wnd)
            self._parent_wnd.windows.append(main_window)
            self.hide()
            # main_window.create_main_ui()


    def on_click_forgot_pw(self):
        write_to_log("Pomnit' Nada")


# class ForgotPassword(QDialog):
#     def __init__(self, parent=None):


class MainWindow(QMainWindow):
    def __init__(self, parent_wnd):
        QMainWindow.__init__(self)

        self._parent_wnd = parent_wnd

        self.label_entry = None
        self.label_receive = None

        self.send_entry = None
        self.receive_entry = None

        self.button_send = None
        self.button_back = None

    def create_main_ui(self):
        uic.loadUi("MainWindowGUI.ui", self)
        self.setFixedSize(500, 700)

        self.label_entry = self.findChild(QLabel, "LabelSend")
        self.label_receive = self.findChild(QLabel, "LabelReceive")

        self.send_entry = self.findChild(QLineEdit, "LineEditSend")
        self.receive_entry = self.findChild(QLineEdit, "LineEditReceive")
        self.receive_entry.setReadOnly(True)

        self.button_send = self.findChild(QPushButton, "ButtonSend")
        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_send.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_back.clicked.connect(self.on_click_back)
        self.button_send.clicked.connect(self.on_click_send)
        self.show()


    def on_click_send(self):
        data = self.send_entry.text()
        self._parent_wnd.send_data(data)
        answer = self._parent_wnd.receive_data()
        if not answer:
            self.send_entry.setText("Server didn't answer...")
        else:
            self.receive_entry.setText(answer)

    def on_click_back(self):
        self._parent_wnd.show()
        self.close()


class RecordWindow(QMainWindow):
    def __init__(self, parent_wnd):
        QMainWindow.__init__(self)

        self._parent_wnd = parent_wnd

        self.label_record = None

        self.button_record = None
        self.button_back = None
        self.create_main_ui()

    def create_main_ui(self):
        uic.loadUi("RecordWndGUI.ui", self)
        self.setFixedSize(500, 500)

        self.label_record = self.findChild(QLabel, "LabelRecord")

        self.button_back = self.findChild(QPushButton, "ButtonBack")
        self.button_back.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_record = self.findChild(QPushButton, "ButtonRecord")
        self.button_record.setStyleSheet("""
        QPushButton {
                    border: 2px solid #00ff00;
                    border-image: url('microphone_img_final.png');
                    }
        QPushButton:hover {
                    border: 2px solid #00ff00;
                    border-image: url('microphone_img_final_hover.png');
                    }
        QPushButton:pressed {
                    border: 2px solid #00ff00;
                    border-image: url('microphone_img_final_pressed.png');
                    }
                """)
        self.button_record.setFixedSize(300, 300)
        self.button_back.clicked.connect(self.on_click_back)
        self.button_record.clicked.connect(self.on_click_record)
        self.show()

    def _record(self):
        self._parent_wnd.record_wav("recording.wav")
        self._parent_wnd.send_wav("recording.wav")
        self.label_record.setText("Recording done!")
        time.sleep(3)
        self.label_record.setText("Record")

    def on_click_record(self):
        if not self._parent_wnd.is_recording:
            self.label_record.setText("Recording...")
            self._parent_wnd.cond()
            recording = threading.Thread(target=self._record)
            recording.start()
        else:
            self.label_record.setText("Record")
            self._parent_wnd.cond()

    def on_click_back(self):
        self._parent_wnd.show()
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    Client = CConnectGUI()
    app.exec_()
