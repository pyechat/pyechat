from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QTreeWidget, QTreeWidgetItem, QSplitter, QStackedWidget
from PyQt6.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self, client):
        super().__init__()

        self.client = client
        self.client.received_message.connect(self.on_received_message)

        self.nicklists = {}
        self.nicklist_items = {}
        self.text_areas = {}

        self.layout = QVBoxLayout(self)

        self.splitter = QSplitter(self)
        self.layout.addWidget(self.splitter)
        self.input_line = QLineEdit(self)
        self.layout.addWidget(self.input_line)
        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setHeaderLabel("Channels")
        self.splitter.addWidget(self.tree_widget)
        self.input_line.returnPressed.connect(self.on_return_pressed)
        self.stacked_widget = QStackedWidget(self)
        self.splitter.addWidget(self.stacked_widget)

        self.nicklist_widget = QTreeWidget(self)
        self.nicklist_widget.setHeaderLabel("Nicklist")
        self.splitter.addWidget(self.nicklist_widget)

        self.tree_widget.itemClicked.connect(self.on_item_clicked)

    @pyqtSlot(QTreeWidgetItem, int)
    def on_item_clicked(self, item, column):
        channel = item.text(0)
        self.stacked_widget.setCurrentWidget(self.text_areas[channel])

    @pyqtSlot(str)
    def on_received_message(self, message):
        parts = message.split(' ', 3)
        if len(parts) < 4:
            return
        user, _, channel, text = parts
        user = user[1:].split('!', 1)[0]
        channel = channel if channel.startswith('#') else user
        text = text[1:]

        # Check if the message is a /NAMES list
        if '!' not in user and text.startswith("#"):
            # Extract the nicknames and add them to the nicklist
            nicknames = text.split(':')[1].split()
            self.nicklists[channel] = set(nicknames)
        else:
            self.add_channel_item(channel)
            self.text_areas[channel].append(f'<{user}> {text}')

        # Update the nicklist display
        self.nicklist_widget.clear()
        if channel in self.nicklists:
            if channel not in self.nicklist_items:
                self.nicklist_items[channel] = QTreeWidgetItem(self.nicklist_widget)
                self.nicklist_items[channel].setText(0, channel)
            channel_item = self.nicklist_items[channel]
            channel_item.takeChildren()
            for nick in self.nicklists[channel]:
                nick_item = QTreeWidgetItem(channel_item)
                nick_item.setText(0, nick)

    @pyqtSlot()
    def on_return_pressed(self):
        message = self.input_line.text()
        self.input_line.clear()

        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return

        channel = current_item.text(0)
        if message.startswith('/'):
            if ' ' in message:
                command, args = message[1:].split(' ', 1)
                if command in ['join', 'part']:
                    channel = args.split(' ', 1)[0]
                    self.client.send_command(f'{command.upper()} {channel}')
                    if command == 'join':
                        self.add_channel_item(channel)
        else:
            self.client.send_command(f'PRIVMSG {channel} :{message}')
            self.text_areas[channel].append(f'<{self.client.nickname}> {message}')

    def add_channel_item(self, channel):
        if channel not in self.text_areas:
            text_area = QTextEdit(self)
            text_area.setReadOnly(True)
            self.text_areas[channel] = text_area
            self.stacked_widget.addWidget(text_area)
            channel_item = QTreeWidgetItem(self.tree_widget)
            channel_item.setText(0, channel)