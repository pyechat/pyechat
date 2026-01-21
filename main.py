from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from src.irc.irc_client import IRCClient
from src.gui.main_window import MainWindow
import sys

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("PyeChat")
    app.setDesktopFileName("pyechat.desktop")
    app.setWindowIcon(QIcon('/home/colby/projects/pyechat/pyechat.ico'))

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
