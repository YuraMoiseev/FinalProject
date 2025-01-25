import threading
import time
import os
from Protocol import *
from CServerBL import CServerBL
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QMainWindow, QLabel, QLineEdit, QGraphicsOpacityEffect, \
    QWidget, QComboBox
from PyQt5.QtCore import QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup, QPoint
from PyQt5 import uic

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
        self.windows = []

        self.create_homepage_ui()
        self._server_thread = threading.Thread(target=self.start_server)
        self._server_thread.start()

    def on_click_stop(self):
        self.stop_server()
        self._parent_wnd.show()
        self.close()

    def create_homepage_ui(self):
        uic.loadUi("GUI/UIs/ServerMainPageGUI.ui", self)
        self.setFixedSize(600, 475)

        self.welcome_label = self.findChild(QLabel, "LabelTitle")
        self.button_add_song_wnd = self.findChild(QPushButton, "ButtonAddSongWnd")
        self.button_add_song_wnd.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_add_song_wnd.setFixedSize(200, 50)
        self.button_requests_wnd = self.findChild(QPushButton, "ButtonRequestWnd")
        self.button_requests_wnd.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_requests_wnd.setFixedSize(200, 50)
        self.button_stop = self.findChild(QPushButton, "ButtonStop")
        self.button_stop.setStyleSheet(BUTTON_STYLE_SHEET)

        self.button_add_song_wnd.clicked.connect(self.on_click_add_song_wnd)
        self.button_requests_wnd.clicked.connect(self.on_click_requests_wnd)
        self.button_stop.clicked.connect(self.on_click_stop)

        self.show()

    def on_click_add_song_wnd(self):
        pass

    def on_click_requests_wnd(self):
        pass


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



if __name__ == "__main__":
    app = QApplication([])
    server = CHostGUI()
    app.exec_()





