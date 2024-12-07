from protocol import *
from CClientBL import CClientBL
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QMainWindow, QLabel, QLineEdit, QGraphicsOpacityEffect
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
        self.port_entry = self.findChild(QLineEdit, "LineEditPort")
        self.port_entry.setText(str(PORT))

        self.connect_button = self.findChild(QPushButton, "ButtonConnect")
        self.connect_button.clicked.connect(self.on_click_connect)
        self.show()

    def on_click_connect(self):
        def back_home():
            self.show()
        self.client = CClientGUI(host=self.host_entry.text(), port=int(self.port_entry.text()), callback_back=back_home)
        self.hide()


class CClientGUI(CClientBL, QMainWindow):
    def __init__(self, host, port, callback_back=None):
        CClientBL.__init__(self, host, port)
        QMainWindow.__init__(self)

        self.callback_home = callback_back

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
        self.button_back.clicked.connect(self.on_click_back)
        self.show()

    def on_click_back(self):
        self.callback_home()
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
        self.button_reg.setFixedSize(200, 50)
        self.button_login = self.findChild(QPushButton, "ButtonLogin")
        self.button_login.setFixedSize(200, 50)
        self.button_back = self.findChild(QPushButton, "ButtonBack")

        self.button_reg.clicked.connect(self.on_click_register)
        self.button_login.clicked.connect(self.on_click_login)
        self.button_back.clicked.connect(self.on_click_back)

        self.window_animation()

        self.show()

    def on_click_register(self):

        def callback_register(data):
            write_to_log(data)
            self.send_data(f"Register>{data}")
            recv = self.receive_data()
            write_to_log(recv)
            return recv == REG_SUCCESS

        def back_home():
            self.show()

        obj = CLoginGUI(callback_home=back_home, callback_register=callback_register)
        self.windows.append(obj)
        self.hide()
        obj.create_register_ui()

    def on_click_login(self):

        def callback_login(data):
            self.send_data(f"Login>{data}")
            recv = self.receive_data()
            write_to_log(recv)
            return recv == LOGIN_SUCCESS, recv

        def back_home():
            self.show()

        def login_user():
            def send(data):
                self.send_data(data)
                answer = self.receive_data()
                return answer

            if any(isinstance(i, CLoginGUI) for i in self.windows):
                self.windows.clear()
            main_window = MainWindow(callback_home=back_home,callback_send=send)
            self.windows.append(main_window)
            self.hide()
            main_window.create_main_ui()


        obj = CLoginGUI(callback_home=back_home, callback_login=callback_login, callback_login_user=login_user)
        self.windows.append(obj)
        self.hide()
        obj.create_login_ui()


class CLoginGUI(QDialog):
    def __init__(self, callback_home=None, callback_register=None, callback_login=None, callback_login_user=None):
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

        self._callback_register = callback_register
        self._callback_login = callback_login
        self._callback_home = callback_home
        self._callback_login_user = callback_login_user

    def create_login_ui(self):
        uic.loadUi("LoginGUI.ui", self)
        self.setFixedSize(500, 700)

        self.label_login_fail = self.findChild(QLabel, "LabelLoginFail")
        self.label_login_fail.hide()

        self.label_login = self.findChild(QLabel, "LabelLogin")
        self.login_entry = self.findChild(QLineEdit, "LineEditLogin")

        self.label_password = self.findChild(QLabel, "LabelPassword")
        self.password_entry = self.findChild(QLineEdit, "LineEditPassword")
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.button_login = self.findChild(QPushButton, "ButtonLogin")
        self.button_forgot_pw = self.findChild(QPushButton, "ButtonForgotPW")
        self.button_back = self.findChild(QPushButton, "ButtonBack")


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

    def back_to_home(self):
        self._callback_home()
        self.close()

    def on_click_register(self):
        login_text = self.login_entry.text()
        password_text = self.password_entry.text()
        email_text = self.email_entry.text()
        data = {"login": login_text, "email": email_text, "password": password_text}
        success = self._callback_register(data)
        if not success:
            self.label_reg_fail.show()
        else:
            self.back_to_home()

    def on_click_login(self):
        login_text = self.login_entry.text()
        password_text = self.password_entry.text()
        data = {"login": login_text, "password": password_text}
        success = self._callback_login(data)
        if not success[0]:
            self.label_login_fail.setText(success[1])
            self.label_login_fail.show()
        else:
            self._callback_login_user()


    def on_click_forgot_pw(self):
        write_to_log("Pomnit' Nada")


class MainWindow(QMainWindow):
    def __init__(self, callback_home=None, callback_send=None):
        QMainWindow.__init__(self)

        self._callback_home = callback_home
        self._callback_send = callback_send

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
        self.button_back.clicked.connect(self.on_click_back)
        self.button_send.clicked.connect(self.on_click_send)
        self.show()


    def on_click_send(self):
        data = self.send_entry.text()
        answer = self._callback_send(data)
        if not answer:
            self.send_entry.setText("Server didn't answer...")
        else:
            self.receive_entry.setText(answer)

    def on_click_back(self):
        self._callback_home()
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    Client = CConnectGUI()
    app.exec_()
