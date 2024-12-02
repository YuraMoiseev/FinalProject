import sys
from protocol import *
from CClientBL import CClientBL
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit, QMainWindow, QLabel
from PyQt5 import uic


class CClientGUI(CClientBL, QMainWindow):
    def __init__(self, host, port):
        CClientBL.__init__(self, host, port)
        QMainWindow.__init__(self)

        self.label = None
        self.button_reg = None
        self.button_login = None

        self.create_homepage_ui()

    def create_homepage_ui(self):
        uic.loadUi("TempUI.ui", self)

        self.label = self.findChild(QLabel, "label")
        self.button_reg = self.findChild(QPushButton, "pushButton")
        self.button_login = self.findChild(QPushButton, "pushButton_2")

        self.button_reg.clicked.connect(self.on_click_register)
        self.button_login.clicked.connect(self.on_click_login)

        self.show()

    def on_click_register(self):
        print("Register")

    def on_click_login(self):
        print("Login")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    Client = CClientGUI(CLIENT_HOST, PORT)
    app.exec_()