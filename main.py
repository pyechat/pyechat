import sys
from PyQt5.QtWidgets import QApplication
from irc_client import IRCClient
from app import App

if __name__ == '__main__':
    app = QApplication(sys.argv)

    client = IRCClient("irc.rizon.net", 6667, "elitechat", "#ct")
    client.start()

    ex = App(client)
    ex.show()

    client.new_message.connect(ex.update_text)
    client.joined_channel.connect(ex.add_channel)
    client.sent_command.connect(ex.show_command)

    sys.exit(app.exec_())
