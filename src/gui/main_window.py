from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QTextEdit, QLineEdit, QLabel
from PyQt6.QtCore import Qt
from src.irc.irc_client import IRCClient  # Assuming you have an irc_client.py file with IRCClient class

class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()

        self.setWindowTitle("PyeChat")
        self.setGeometry(100, 100, 800, 600)

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.mainLayout = QHBoxLayout(self.centralWidget)
        self.leftLayout = QVBoxLayout()
        self.middleLayout = QVBoxLayout()
        self.rightLayout = QVBoxLayout()
        self.nickLists = {}
        self.channelList = QListWidget()
        self.nickList = QListWidget()
        self.chatWindow = QTextEdit()
        self.inputText = QLineEdit()
        self.topicLabel = QLabel()
        self.middleLayout.insertWidget(0, self.topicLabel)
        self.channelList.setMaximumWidth(150)
        self.nickList.setMaximumWidth(150)

        self.leftLayout.addWidget(self.channelList)
        self.middleLayout.addWidget(self.chatWindow)
        self.middleLayout.addWidget(self.inputText)
        self.rightLayout.addWidget(self.nickList)

        self.mainLayout.addLayout(self.leftLayout)
        self.mainLayout.addLayout(self.middleLayout)
        self.mainLayout.addLayout(self.rightLayout)

        #self.irc_client = IRCClient("irc.technet.chat", 6667, "pyechat", "pyechat", "")
        self.irc_client = client
        self.irc_client.received_message.connect(self.chatWindow.append)
        self.irc_client.received_nick_list.connect(self.updateNickList)
        self.irc_client.received_topic.connect(self.updateTopic)
        self.irc_client.connect_to_host()
        self.channelList.itemClicked.connect(self.changeChannel)
        self.inputText.returnPressed.connect(self.sendChatMessage)

        self.channelList.addItem("TechNet")

    def updateTopic(self, topic):
        self.topicLabel.setText(topic)

    def changeChannel(self, item):
        new_channel = item.text()
        self.irc_client.switch_channel(new_channel)
        self.nickList.clear()
        self.irc_client.get_nick_list()

    def sendChatMessage(self):
        message = self.inputText.text()
        if message:
            if message.startswith('/'):
                command = message[1:]
                self.irc_client.send_command(command)
                if command.startswith('join '):
                    channel = command.split(' ', 1)[1]
                    self.channelList.addItem(channel)
            else:
                self.irc_client.send_command(f'PRIVMSG {self.irc_client.channel} :{message}')
                self.chatWindow.append(f'<{self.irc_client.nickname}> {message}')  # Append the message to the chatWindow
            self.inputText.clear()

    def openPrivateMessage(self, user):
        self.irc_client.send_command(f'QUERY {user}')
        self.channelList.addItem(user)

    def updateNickList(self, channel_nick):
        channel, nick = channel_nick
        if channel == self.irc_client.channel:
            if nick not in [self.nickList.item(i).text() for i in range(self.nickList.count())]:
                self.nickList.addItem(nick)
            else:
                items = self.nickList.findItems(nick, Qt.MatchExactly)
                if items:
                    self.nickList.takeItem(self.nickList.row(items[0]))