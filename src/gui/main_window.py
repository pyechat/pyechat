from PyQt6.QtWidgets import QMainWindow, QWidget, QColorDialog, QHBoxLayout, QVBoxLayout, QListWidget, QTextEdit, QLineEdit, QCheckBox, QLabel, QMenuBar, QMenu, QStatusBar, QDialog, QPushButton, QFontDialog, QFormLayout, QDialogButtonBox, QSpinBox, QCheckBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from src.irc.irc_client import IRCClient
import json

class NetworkListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Network List")
        self.setGeometry(100, 100, 300, 200)  # Adjust the size of the window

        self.layout = QVBoxLayout(self)

        # Create network list
        self.networkList = QListWidget()

        # Populate network list
        networks = ["Network1", "Network2", "Network3"]  # Replace with your actual networks
        self.networkList.addItems(networks)

        # Add network list to layout
        self.layout.addWidget(self.networkList)

        # Create connect button
        self.connectButton = QPushButton("Connect", self)
        self.connectButton.clicked.connect(self.connectToNetwork)
        self.layout.addWidget(self.connectButton)

        self.setLayout(self.layout)
        self.editButton = QPushButton("Edit", self)
        self.editButton.clicked.connect(self.editNetwork)
        self.layout.addWidget(self.editButton)

        self.setLayout(self.layout)

    def connectToNetwork(self):
        current_item = self.networkList.currentItem()
        if current_item is not None:
            network = current_item.text()
            # Add your code here to connect to the selected network
            print(f"Connecting to {network}")
        else:
            print("No network selected")
                       
    def editNetwork(self):
        current_item = self.networkList.currentItem()
        if current_item is not None:
            network = current_item.text()
            self.editDialog = NetworkEditDialog(network, self)
            self.editDialog.show()
        else:
            print("No network selected")

class NetworkEditDialog(QDialog):
    def __init__(self, network, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Edit {network}")
        self.setGeometry(100, 100, 300, 200)

        self.layout = QFormLayout(self)

        self.hostnameLineEdit = QLineEdit()
        self.portSpinBox = QSpinBox()
        self.portSpinBox.setRange(1, 65535)
        self.nickLineEdit = QLineEdit()
        self.realNameLineEdit = QLineEdit()
        self.sslCheckBox = QCheckBox()

        self.layout.addRow("Hostname:", self.hostnameLineEdit)
        self.layout.addRow("Port:", self.portSpinBox)
        self.layout.addRow("Nick:", self.nickLineEdit)
        self.layout.addRow("Real Name:", self.realNameLineEdit)
        self.layout.addRow("SSL:", self.sslCheckBox)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addRow(self.buttonBox)

        self.setLayout(self.layout)

    def accept(self):
        # Add your code here to handle the input data
        print(f"Hostname: {self.hostnameLineEdit.text()}")
        print(f"Port: {self.portSpinBox.value()}")
        print(f"Nick: {self.nickLineEdit.text()}")
        print(f"Real Name: {self.realNameLineEdit.text()}")
        print(f"SSL: {self.sslCheckBox.isChecked()}")
        super().accept()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 300, 200)  # Adjust the size of the window

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Choose your settings:")
        self.layout.addWidget(self.label)

        # Add checkboxes
        self.checkBox1 = QCheckBox("Setting 1", self)
        self.layout.addWidget(self.checkBox1)

        self.checkBox2 = QCheckBox("Setting 2", self)
        self.layout.addWidget(self.checkBox2)

        self.checkBox3 = QCheckBox("Setting 3", self)
        self.layout.addWidget(self.checkBox3)

        # Add font buttons
        self.fontButton = QPushButton("Choose Chat Font", self)
        self.fontButton.clicked.connect(parent.openFontDialog)
        self.layout.addWidget(self.fontButton)

        self.nickFontButton = QPushButton("Choose Nick Font", self)
        self.nickFontButton.clicked.connect(parent.openNickFontDialog)
        self.layout.addWidget(self.nickFontButton)

        self.channelFontButton = QPushButton("Choose Channel Font", self)
        self.channelFontButton.clicked.connect(parent.openChannelFontDialog)
        self.layout.addWidget(self.channelFontButton)

        # Add OK button
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)
        self.layout.addWidget(self.okButton)

        self.setLayout(self.layout)

        # Add color buttons
        self.nickColorButton = QPushButton("Choose Nick Color", self)
        self.nickColorButton.clicked.connect(parent.openNickColorDialog)
        self.layout.addWidget(self.nickColorButton)

        self.channelColorButton = QPushButton("Choose Channel Color", self)
        self.channelColorButton.clicked.connect(parent.openChannelColorDialog)
        self.layout.addWidget(self.channelColorButton)

        self.chatColorButton = QPushButton("Choose Chat Color", self)
        self.chatColorButton.clicked.connect(parent.openChatColorDialog)
        self.layout.addWidget(self.chatColorButton)

class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()

        # Set window properties
        self.setWindowTitle("PyeChat")
        self.setGeometry(50, 50, 1200, 800)

        # Set stylesheet
        self.setStyleSheet("""
            QWidget {
                font-size: 16px;
                background-color: #ffffff;
            }
            QListWidget, QTextEdit, QLineEdit {
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                border: 1px solid #999999;
                background:white;
                width:10px;  
                margin: 0px 0 0px 0;
            }
            QScrollBar::handle:vertical {    
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop: 0 rgb(32, 47, 130), stop: 0.5 rgb(32, 47, 130), stop:1 rgb(32, 47, 130));
                min-height: 60px;  # Increase this value to make the scrollbar handle longer
            }
            QMenuBar::item {
                padding: 5px;
            }
        """)

        # Rest of the __init__ function...


        # Create central widget and layout
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QHBoxLayout(self.centralWidget)
        self.settingsAction = QAction(QIcon("settings_icon.png"), "Settings", self)
        self.settingsAction.triggered.connect(self.openSettingsDialog)

        # Create a menu bar
        self.menuBar = QMenuBar()

        # Create a menu
        self.fileMenu = QMenu("PyeChat", self)
        self.settingsMenu = QMenu("Settings", self)

        # Create actions
        self.networkListAction = QAction(QIcon("network_list_icon.png"), "Network List", self)
        self.networkListAction.triggered.connect(self.openNetworkListDialog)
        self.settingsAction = QAction(QIcon("settings_icon.png"), "Settings", self)
        self.settingsAction.triggered.connect(self.openSettingsDialog)
        self.exitAction = QAction(QIcon("exit_icon.png"), "Exit", self)

        # Add actions to the menu
        self.fileMenu.addAction(self.networkListAction)
        self.settingsMenu.addAction(self.settingsAction)
        self.fileMenu.addAction(self.exitAction)


        # Add actions to the menu
        self.settingsMenu.addAction(self.settingsAction)
        self.fileMenu.addAction(self.exitAction)

        # Add menu to the menu bar
        self.menuBar.addMenu(self.fileMenu)
        self.menuBar.addMenu(self.settingsMenu)

        # Set the menu bar
        self.setMenuBar(self.menuBar)

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Create layouts
        self.leftLayout = QVBoxLayout()
        self.middleLayout = QVBoxLayout()
        self.rightLayout = QVBoxLayout()

        # Create widgets
        self.nickLists = {}
        self.channelList = QListWidget()
        self.nickList = QListWidget()
        self.chatWindow = QTextEdit()
        self.inputText = QLineEdit()
        self.topicLabel = QLabel()

        # Configure widgets
        self.middleLayout.insertWidget(0, self.topicLabel)
        self.channelList.setMaximumWidth(150)
        self.nickList.setMaximumWidth(150)

        # Add widgets to layouts
        self.leftLayout.addWidget(self.channelList)
        self.middleLayout.addWidget(self.chatWindow)
        self.middleLayout.addWidget(self.inputText)
        self.rightLayout.addWidget(self.nickList)

        # Add layouts to main layout
        self.mainLayout.addLayout(self.leftLayout)
        self.mainLayout.addLayout(self.middleLayout)
        self.mainLayout.addLayout(self.rightLayout)

        # IRC client setup
        self.irc_client = client
        self.irc_client.received_message.connect(self.chatWindow.append)
        self.irc_client.received_nick_list.connect(self.updateNickList)
        self.irc_client.received_topic.connect(self.updateTopic)
        self.irc_client.connect_to_host()

        # Connect signals
        self.channelList.itemClicked.connect(self.changeChannel)
        self.inputText.returnPressed.connect(self.sendChatMessage)

        # Add initial channel
        self.channelList.addItem("Rizon")

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
                if command.startswith('nick '):
                    new_nick = command.split(' ', 1)[1]
                    self.irc_client.nickname = new_nick
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
                items = self.nickList.findItems(nick, Qt.MatchFlag.MatchExactly)
                if items:
                    self.nickList.takeItem(self.nickList.row(items[0]))

    def openSettingsDialog(self):
        self.settingsDialog = SettingsDialog(self)
        self.settingsDialog.show()

    def openFontDialog(self):
        fontDialog = QFontDialog(self)
        fontDialog.fontSelected.connect(self.setChatFont)
        fontDialog.open()

    def setChatFont(self, font):
        self.chatWindow.setFont(font)

    def openNickFontDialog(self):
        fontDialog = QFontDialog(self)
        fontDialog.fontSelected.connect(self.setNickFont)
        fontDialog.open()

    def setNickFont(self, font):
        self.nickList.setFont(font)

    def openChannelFontDialog(self):
        fontDialog = QFontDialog(self)
        fontDialog.fontSelected.connect(self.setChannelFont)
        fontDialog.open()

    def setChannelFont(self, font):
        self.channelList.setFont(font)

    def openNickColorDialog(self):
        colorDialog = QColorDialog(self)
        colorDialog.colorSelected.connect(self.setNickColor)
        colorDialog.open()

    def setNickColor(self, color):
        self.nickList.setStyleSheet(f"background-color: {color.name()}")

    def openChannelColorDialog(self):
        colorDialog = QColorDialog(self)
        colorDialog.colorSelected.connect(self.setChannelColor)
        colorDialog.open()

    def setChannelColor(self, color):
        self.channelList.setStyleSheet(f"background-color: {color.name()}")

    def openChatColorDialog(self):
        colorDialog = QColorDialog(self)
        colorDialog.colorSelected.connect(self.setChatColor)
        colorDialog.open()

    def setChatColor(self, color):
        self.chatWindow.setStyleSheet(f"background-color: {color.name()}")

    def openNetworkListDialog(self):
        self.networkListDialog = NetworkListDialog(self)
        self.networkListDialog.show()
