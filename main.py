from PyQt6.QtWidgets import QApplication
from src.irc.irc_client import IRCClient
from src.gui.main_window import MainWindow
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Define your default connection values
    host = "irc.rizon.net"
    port = 6667 # This should be a string representing an integer
    nick = "your_nick"
    realname = "your_realname"
    channel = "your_channel"
    use_ssl = False  # or True

    client = IRCClient(host, int(port), nick, realname, channel, use_ssl)  # Convert port to int
    client.connect_to_host()

    window = MainWindow(client)
    window.show()

    sys.exit(app.exec())
