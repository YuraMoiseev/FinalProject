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
        self.button_reg = None
        self.button_login = None
        self.button_back = None
        self.windows = []

        self.welcome_label_anim = None
        self.buttons_anim = None
        self.window_anim = None

        self.start_server()


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


