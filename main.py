from PyQt5.QtWidgets import QApplication
from src.irc.irc_client import IRCClient
from src.gui.connect_dialog import ConnectDialog
from src.gui.main_window import MainWindow
import sys
from PyQt5.QtWidgets import QApplication, QDialog

if __name__ == '__main__':
    app = QApplication(sys.argv)

    dialog = ConnectDialog()
    if dialog.exec() == QDialog.Accepted:
        host, port, nick, realname, channel = dialog.get_values()
        client = IRCClient(host, port, nick, realname, channel)
        client.connect_to_host()

        window = MainWindow(client)
        window.show()

        sys.exit(app.exec())