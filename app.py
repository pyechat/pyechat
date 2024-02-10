from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QListWidget, QLineEdit
from irc_client import IRCClient

class App(QWidget):
    def __init__(self, irc_client):
        super().__init__()
        self.title = 'EliteChat'
        self.irc_client = irc_client
        self.initUI()

    def initUI(self):
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

    def update_text(self, message):
        self.text_area.append(message)

    def add_channel(self, channel):
        self.channel_list.addItem(channel)

    def show_command(self, command):
        self.text_area.append("Sent command: " + command)
