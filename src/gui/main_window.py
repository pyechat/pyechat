from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QTabWidget

class MainWindow(QWidget):
    def __init__(self, client):
        super().__init__()

        self.client = client
        self.client.received_message.connect(self.on_received_message)

        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget(self)
        self.layout.addWidget(self.tab_widget)

        self.text_areas = {}

        self.input_line = QLineEdit(self)
        self.input_line.returnPressed.connect(self.on_return_pressed)
        self.layout.addWidget(self.input_line)

    @pyqtSlot(str)
    def on_received_message(self, message):
        parts = message.split(' ', 3)
        if len(parts) < 4:
            return
        user, _, channel, text = parts
        user = user[1:].split('!', 1)[0]
        channel = channel if channel.startswith('#') else user
        text = text[1:]

        self.add_channel_tab(channel)
        self.text_areas[channel].append(f'<{user}> {text}')

    @pyqtSlot()
    def on_return_pressed(self):
        message = self.input_line.text()
        self.input_line.clear()

        channel = self.tab_widget.tabText(self.tab_widget.currentIndex())
        if message.startswith('/'):
            if ' ' in message:
                command, args = message[1:].split(' ', 1)
                if command in ['join', 'part']:
                    channel = args.split(' ', 1)[0]
                    self.client.send_command(f'{command.upper()} {channel}')
                    if command == 'join':
                        self.add_channel_tab(channel)
        else:
            self.client.send_command(f'PRIVMSG {channel} :{message}')
            self.text_areas[channel].append(f'<{self.client.nickname}> {message}')

    def add_channel_tab(self, channel):
        if channel not in self.text_areas:
            text_area = QTextEdit(self)
            text_area.setReadOnly(True)
            self.text_areas[channel] = text_area
            self.tab_widget.addTab(text_area, channel)