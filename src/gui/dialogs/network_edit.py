"""Network edit dialog for configuring IRC network connection details."""
from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QSpinBox, 
                             QCheckBox, QTextEdit, QComboBox, QDialogButtonBox)


class NetworkEditDialogue(QDialog):
    """Dialog for editing IRC network connection settings."""
    
    def __init__(self, nw, parent=None):
        super().__init__(parent)
        self.nw = nw
        self.setWindowTitle(f"Edit {nw['name']}")
        self.layout = QFormLayout(self)
        
        self.name = QLineEdit(nw['name'])
        self.host = QLineEdit(nw['host'])
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(nw['port'])
        self.nick = QLineEdit(nw['nick'])
        self.realname = QLineEdit(nw['realname'])
        self.channels = QLineEdit(", ".join(nw.get('channels', [])))
        self.ssl = QCheckBox()
        self.ssl.setChecked(nw.get('use_ssl', False))
        self.pwd = QLineEdit(nw.get('password', ""))
        self.pwd.setEchoMode(QLineEdit.Password)
        
        self.sasl_method = QComboBox()
        self.sasl_method.addItems(["None", "PLAIN", "EXTERNAL"])
        self.sasl_method.setCurrentText(nw.get('sasl_method', "None"))
        self.sasl_user = QLineEdit(nw.get('sasl_user', ""))
        self.sasl_pass = QLineEdit(nw.get('sasl_pass', ""))
        self.sasl_pass.setEchoMode(QLineEdit.Password)
        self.auto_cmds = QTextEdit("\n".join(nw.get('auto_commands', [])))
        self.auto_cmds.setPlaceholderText(
            "One command per line, e.g.\nPRIVMSG NickServ :IDENTIFY password"
        )
        self.auto_cmds.setMaximumHeight(80)

        # OperServ nick (optional) - used by OperServ command submenu
        self.operserv = QLineEdit(nw.get('operserv', 'OperServ'))
        self.layout.addRow("OperServ nick:", self.operserv)

        self.layout.addRow("Name:", self.name)
        self.layout.addRow("Host:", self.host)
        self.layout.addRow("Port:", self.port)
        self.layout.addRow("Nick:", self.nick)
        self.layout.addRow("Real Name:", self.realname)
        self.layout.addRow("Channels:", self.channels)
        self.layout.addRow("SSL:", self.ssl)
        self.layout.addRow("Password:", self.pwd)
        self.layout.addRow("SASL Method:", self.sasl_method)
        self.layout.addRow("SASL User:", self.sasl_user)
        self.layout.addRow("SASL Pass:", self.sasl_pass)
        self.layout.addRow("Auto-Commands:", self.auto_cmds)

        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        self.layout.addRow(self.btns)

    def accept(self):
        """Save the network configuration when OK is clicked."""
        self.nw.update({
            "name": self.name.text(),
            "host": self.host.text(),
            "port": self.port.value(),
            "nick": self.nick.text(),
            "realname": self.realname.text(),
            "channels": [c.strip() for c in self.channels.text().split(',') if c.strip()],
            "use_ssl": self.ssl.isChecked(),
            "password": self.pwd.text(),
            "sasl_method": self.sasl_method.currentText() if self.sasl_method.currentText() != "None" else None,
            "sasl_user": self.sasl_user.text(),
            "sasl_pass": self.sasl_pass.text(),
            "auto_commands": [l.strip() for l in self.auto_cmds.toPlainText().split('\n') if l.strip()],
            "operserv": self.operserv.text().strip() or None
        })
        super().accept()
