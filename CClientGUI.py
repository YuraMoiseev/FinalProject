from protocol import *
from CClientBL import CClientBL
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QMainWindow, QLabel, QLineEdit
from PyQt5 import uic
import json


class CClientGUI(CClientBL, QMainWindow):
    def __init__(self, host, port):
        CClientBL.__init__(self, host, port)
        QMainWindow.__init__(self)

        self.label = None
        self.button_reg = None
        self.button_login = None
        self.windows = []

        self._client_socket = self.connect()
        if self._client_socket is not None:
            self.create_homepage_ui()
        else:
            self.create_error_wnd()

    def create_error_wnd(self):
        uic.loadUi('ErrorWindowGUI.ui', self)
        self.setFixedSize(600, 400)
        self.show()

    def create_homepage_ui(self):
        uic.loadUi("HomePageGUI.ui", self)
        self.setFixedSize(600, 400)

        self.label = self.findChild(QLabel, "LabelWelcome")
        self.button_reg = self.findChild(QPushButton, "ButtonRegister")
        self.button_reg.setFixedSize(200, 50)
        self.button_login = self.findChild(QPushButton, "ButtonLogin")
        self.button_login.setFixedSize(200, 50)

        self.button_reg.clicked.connect(self.on_click_register)
        self.button_login.clicked.connect(self.on_click_login)

        self.show()


    def on_click_register(self):

        def callback_register(data: json):
            # will be updated to send request to the server
            pass

        def back_home():
            self.show()

        obj = CLoginGUI(callback_home=back_home, callback_register=callback_register, callback_login=None)
        self.windows.append(obj)
        self.hide()
        obj.create_register_ui()

    def on_click_login(self):

        def callback_login(data: json):
            # will be updated to send request to the server
            pass

        def back_home():
            self.show()

        obj = CLoginGUI(callback_home=back_home, callback_register=None, callback_login=callback_login)
        self.windows.append(obj)
        self.hide()
        obj.create_login_ui()


class CLoginGUI(QDialog):
    def __init__(self, callback_home=None, callback_register=None, callback_login=None):
        QDialog.__init__(self)

        self.label_login = None
        self.label_password = None
        self.label_email = None

        self.login_entry = None
        self.password_entry = None
        self.email_entry = None

        self.button_back = None
        self.button_register = None
        self.button_login = None
        self.button_forgot_pw = None

        self._callback_register = callback_register
        self._callback_login = callback_login
        self._callback_home = callback_home

    def create_login_ui(self):
        uic.loadUi("LoginGUI.ui", self)
        self.setFixedSize(500, 700)

        self.label_login = self.findChild(QLabel, "LabelLogin")
        self.login_entry = self.findChild(QLineEdit, "LineEditLogin")

        self.label_password = self.findChild(QLabel, "LabelPassword")
        self.password_entry = self.findChild(QLineEdit, "LineEditPassword")
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.button_login = self.findChild(QPushButton, "ButtonLogin")
        self.button_forgot_pw = self.findChild(QPushButton, "ButtonForgotPW")
        self.button_back = self.findChild(QPushButton, "ButtonBack")


        self.button_login.clicked.connect(self.on_click_login)
        self.button_forgot_pw.clicked.connect(self.forgot_pw)
        self.button_back.clicked.connect(self.back_to_home)

        self.show()

    def create_register_ui(self):
        uic.loadUi("RegisterWindowGUI.ui", self)
        self.setFixedSize(500, 700)

        self.label_login = self.findChild(QLabel, "LabelLogin")
        self.login_entry = self.findChild(QLineEdit, "LineEditLogin")

        self.label_email = self.findChild(QLabel, "LabelEmail")
        self.email_entry = self.findChild(QLineEdit, "LineEditEmail")

        self.label_password = self.findChild(QLabel, "LabelPassword")
        self.password_entry = self.findChild(QLineEdit, "LineEditPassword")
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.button_register = self.findChild(QPushButton, "ButtonRegister")
        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_register.clicked.connect(self.on_click_register)
        self.button_back.clicked.connect(self.back_to_home)

        self.show()


    def on_click_register(self):
        login_text = self.login_entry.text()
        password_text = self.password_entry.text()
        data = {"login": login_text, "password": password_text}
        self._callback_register(data)

    def back_to_home(self):
        self._callback_home()
        self.close()


    def on_click_login(self):
        login_text = self.login_entry.text()
        password_text = self.password_entry.text()
        data = {"login": login_text, "password": password_text}
        self._callback_login(data)

    def forgot_pw(self):
        print("Pomnit' Nada")


if __name__ == "__main__":
    app = QApplication([])
    Client = CClientGUI(CLIENT_HOST, PORT)
    app.exec_()
