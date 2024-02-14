from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel, QApplication

class ConnectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Connect to IRC Server")

        self.layout = QVBoxLayout(self)

        self.host_label = QLabel("Host:", self)
        self.layout.addWidget(self.host_label)
        self.host_input = QLineEdit(self)
        self.host_input.setText("irc.rizon.net")
        self.layout.addWidget(self.host_input)

        self.port_label = QLabel("Port:", self)
        self.layout.addWidget(self.port_label)
        self.port_input = QLineEdit(self)
        self.port_input.setText("6667")
        self.layout.addWidget(self.port_input)

        self.nick_label = QLabel("Nickname:", self)
        self.layout.addWidget(self.nick_label)
        self.nick_input = QLineEdit(self)
        self.nick_input.setText("pyechat")
        self.layout.addWidget(self.nick_input)

        self.realname_label = QLabel("Real name:", self)
        self.layout.addWidget(self.realname_label)
        self.realname_input = QLineEdit(self)
        self.realname_input.setText("Pyechat: https://pyechat.github.io")
        self.layout.addWidget(self.realname_input)

        self.channel_label = QLabel("Channel:", self)
        self.layout.addWidget(self.channel_label)
        self.channel_input = QLineEdit(self)
        self.channel_input.setText("#pyechat")
        self.layout.addWidget(self.channel_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_values(self):
        return self.host_input.text(), int(self.port_input.text()), self.nick_input.text(), self.realname_input.text(), self.channel_input.text()
    
    def closeEvent(self, event):
        QApplication.quit()