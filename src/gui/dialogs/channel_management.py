"""Channel Management dialog: topic, modes, ban list."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt
import datetime

class ChannelManagementDialogue(QDialog):
    def __init__(self, parent, network_name, channel, client):
        super().__init__(parent)
        self.setWindowTitle(f"Channel Management — {channel}")
        self.setMinimumWidth(500)
        self.network_name = network_name
        self.channel = channel
        self.client = client
        self.ban_entries = []
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Topic editor
        t_layout = QHBoxLayout()
        self.topic_label = QLabel("Topic:")
        self.topic_edit = QLineEdit()
        self.topic_set_btn = QPushButton("Set Topic")
        t_layout.addWidget(self.topic_label)
        t_layout.addWidget(self.topic_edit)
        t_layout.addWidget(self.topic_set_btn)
        layout.addLayout(t_layout)

        # Modes editor
        m_layout = QHBoxLayout()
        self.mode_label = QLabel("Modes:")
        self.mode_edit = QLineEdit()
        self.mode_btn = QPushButton("Set Modes")
        m_layout.addWidget(self.mode_label)
        m_layout.addWidget(self.mode_edit)
        m_layout.addWidget(self.mode_btn)
        layout.addLayout(m_layout)

        # Ban list
        self.ban_table = QTableWidget(0, 3)
        self.ban_table.setHorizontalHeaderLabels(["Banmask", "Setter", "Set At"])
        self.ban_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(QLabel("Ban List:"))
        layout.addWidget(self.ban_table)

        bbtn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.add_ban_btn = QPushButton("Add Ban")
        self.remove_ban_btn = QPushButton("Remove Selected")
        bbtn_layout.addWidget(self.refresh_btn)
        bbtn_layout.addWidget(self.add_ban_btn)
        bbtn_layout.addWidget(self.remove_ban_btn)
        layout.addLayout(bbtn_layout)

        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def connect_signals(self):
        self.topic_set_btn.clicked.connect(self.set_topic)
        self.mode_btn.clicked.connect(self.set_mode)
        self.refresh_btn.clicked.connect(self.refresh_banlist)
        self.add_ban_btn.clicked.connect(self.add_ban)
        self.remove_ban_btn.clicked.connect(self.remove_selected)
        # Hook into client signals
        self.client.received_banlist.connect(self._on_ban_item)
        self.client.received_banlist_end.connect(self._on_ban_end)

    def closeEvent(self, event):
        # Disconnect signals
        try:
            self.client.received_banlist.disconnect(self._on_ban_item)
            self.client.received_banlist_end.disconnect(self._on_ban_end)
        except Exception:
            pass
        super().closeEvent(event)

    def set_topic(self):
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "Set Topic", "Topic cannot be empty")
            return
        # TOPIC command
        self.client.send_command(f"TOPIC {self.channel} :{topic}")
        self.status_label.setText("Setting topic...")

    def set_mode(self):
        m = self.mode_edit.text().strip()
        if not m:
            QMessageBox.warning(self, "Set Modes", "Modes string cannot be empty")
            return
        self.client.send_command(f"MODE {self.channel} {m}")
        self.status_label.setText("Setting modes...")

    def refresh_banlist(self):
        self.ban_entries = []
        self.ban_table.setRowCount(0)
        # Request banlist
        self.client.send_command(f"MODE {self.channel} +b")
        self.status_label.setText("Requesting ban list...")

    def _on_ban_item(self, chan, banmask, setter, ts):
        if chan != self.channel: return
        # Add to table
        row = self.ban_table.rowCount()
        self.ban_table.insertRow(row)
        self.ban_table.setItem(row, 0, QTableWidgetItem(banmask))
        self.ban_table.setItem(row, 1, QTableWidgetItem(setter))
        try:
            ts_text = datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M') if ts else ''
        except Exception:
            ts_text = str(ts)
        self.ban_table.setItem(row, 2, QTableWidgetItem(ts_text))

    def _on_ban_end(self, chan):
        if chan != self.channel: return
        self.status_label.setText("Ban list loaded")

    def add_ban(self):
        banmask, ok = QInputDialog.getText(self, "Add Ban", "Ban mask (nick!user@host or *.example.com):")
        if ok and banmask.strip():
            self.client.send_command(f"MODE {self.channel} +b {banmask.strip()}")
            self.status_label.setText("Adding ban...")
            self.refresh_banlist()

    def remove_selected(self):
        sel = self.ban_table.selectedItems()
        if not sel:
            QMessageBox.information(self, "Remove Ban", "No ban selected")
            return
        # Assume first column is banmask
        banmask = sel[0].text()
        self.client.send_command(f"MODE {self.channel} -b {banmask}")
        self.status_label.setText("Removing ban...")
        self.refresh_banlist()
