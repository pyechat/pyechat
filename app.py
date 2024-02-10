from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QWidget, QHBoxLayout, QTextEdit, QListWidget
from PyQt5.QtCore import pyqtSignal
from irc_client import IRCClient
import sys

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("Login to IRC")

        self.layout = QVBoxLayout(self)

        self.hostLabel = QLabel("Hostname:")
        self.nickLabel = QLabel("Nick:")
        self.portLabel = QLabel("Port:")
        self.channelLabel = QLabel("Channel:")

        self.hostInput = QLineEdit(self)
        self.hostInput.setText("irc.rizon.net")  # Default hostname
        self.nickInput = QLineEdit(self)
        self.nickInput.setText("EliteChat")  # Default nick
        self.portInput = QLineEdit(self)
        self.portInput.setText("6667")  # Default port
        self.channelInput = QLineEdit(self)
        self.channelInput.setText("#elitebot")  # Default channel

        self.loginButton = QPushButton("Login", self)
        self.loginButton.clicked.connect(self.accept)

        self.layout.addWidget(self.hostLabel)
        self.layout.addWidget(self.hostInput)
        self.layout.addWidget(self.nickLabel)
        self.layout.addWidget(self.nickInput)
        self.layout.addWidget(self.portLabel)
        self.layout.addWidget(self.portInput)
        self.layout.addWidget(self.channelLabel)
        self.layout.addWidget(self.channelInput)
        self.layout.addWidget(self.loginButton)

    def getInputs(self):
        return self.hostInput.text(), self.nickInput.text(), int(self.portInput.text()), self.channelInput.text()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'EliteChat'
        self.initUI()

    def initUI(self):
        self.loginDialog = LoginDialog(self)
        if self.loginDialog.exec_() == QDialog.Accepted:
            host, nick, port, channel = self.loginDialog.getInputs()
            self.irc_client = IRCClient(host, port, nick, channel)
            self.irc_client.start()

        self.setWindowTitle(self.title)
        self.layout = QHBoxLayout()

        self.channel_list = QListWidget()
        self.layout.addWidget(self.channel_list, 1)

        self.chat_layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.chat_layout.addWidget(self.text_area, 5)

        self.input_line = QLineEdit()
        self.chat_layout.addWidget(self.input_line)

        self.layout.addLayout(self.chat_layout, 10)

        self.setLayout(self.layout)
        self.resize(800, 600)

        self.input_line.returnPressed.connect(self.send_message)

    def send_message(self):
        message = self.input_line.text()
        self.irc_client.ircsend(message)
        self.input_line.clear()

    def update_text(self, source, command, args):
        message = f"{source} | {command} | {args}"
        self.text_area.append(message)

    def add_channel(self, channel):
        self.channel_list.addItem(channel)

    def show_command(self, command):
        self.text_area.append("Sent command: " + command)


def main():
    app = QApplication(sys.argv)

    # Read the stylesheet
    with open('style.qss', 'r') as f:
        stylesheet = f.read()

    # Apply the stylesheet
    app.setStyleSheet(stylesheet)

    ex = App()
    ex.show()

    if ex.irc_client is not None:
        ex.irc_client.new_message.connect(lambda source, command, args: ex.update_text(source, command, args))
        ex.irc_client.joined_channel.connect(ex.add_channel)
        ex.irc_client.sent_command.connect(ex.show_command)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
