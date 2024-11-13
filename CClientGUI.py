import sys
from protocol import *
from CClientBL import CClientBL
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit, QMainWindow, QLabel
from PyQt5 import uic


class CClientGUI(CClientBL):

    def __init__(self, host, port):

        super().__init__(host, port)

        self.app = None
        self.window = None
        self.layout = None

        self.create_ui()

    def create_ui(self):
        self.app = QApplication([])
        self.window = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(QPushButton('Top'))
        self.layout.addWidget(QPushButton('Bottom'))
        self.window.setLayout(self.layout)
        self.window.show()
        self.app.exec()


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        # Load the ui file
        uic.loadUi("LogInTemp.ui", self)

        # Define Widgets
        self.label = self.findChild(QLabel, "label")
        self.button_reg = self.findChild(QPushButton, "pushButton")
        self.button_login = self.findChild(QPushButton, "pushButton_2")
        self.button_reg.clicked.connect(self.Register)
        self.button_login.clicked.connect(self.Login)

        self.show()

    def Register(self):
        print(1)

    def Login(self):
        print(2)


if __name__ == "__main__":
    # Client = CClientGUI(CLIENT_HOST, PORT)
    app = QApplication(sys.argv)
    Wnd = UI()
    app.exec_()


