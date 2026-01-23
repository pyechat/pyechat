"""Network list dialog for managing IRC network connections."""
import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QCheckBox)


class NetworkListDialogue(QDialog):
    """Dialog for selecting and managing IRC network connections."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Network List")
        self.setMinimumSize(400, 300)
        self.layout = QVBoxLayout(self)
        self.networkList = QListWidget()
        self.networks = self.load_networks()
        for nw in self.networks:
            self.networkList.addItem(nw['name'])
        self.layout.addWidget(self.networkList)
        
        self.skip_cb = QCheckBox("Skip Network List on startup")
        self.skip_cb.setChecked(self.parent.settings.get("skip_network_list", False))
        self.skip_cb.toggled.connect(self.on_skip_toggled)
        self.layout.addWidget(self.skip_cb)

        self.btn_layout = QHBoxLayout()
        self.connectBtn = QPushButton("Connect")
        self.connectBtn.clicked.connect(self.connectToNetwork)
        self.editBtn = QPushButton("Edit")
        self.editBtn.clicked.connect(self.editNetwork)
        self.addBtn = QPushButton("Add")
        self.addBtn.clicked.connect(self.addNetwork)
        self.btn_layout.addWidget(self.connectBtn)
        self.btn_layout.addWidget(self.editBtn)
        self.btn_layout.addWidget(self.addBtn)
        self.layout.addLayout(self.btn_layout)

    def on_skip_toggled(self, checked):
        """Handle skip network list checkbox toggle."""
        self.parent.settings["skip_network_list"] = checked
        self.parent.save_settings()

    def load_networks(self):
        """Load network configurations from data/networks.json."""
        networks_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'networks.json')
        networks_path = os.path.abspath(networks_path)
        
        try:
            with open(networks_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_networks(self):
        """Save network configurations to data/networks.json."""
        networks_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'networks.json')
        networks_path = os.path.abspath(networks_path)
        
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(networks_path), exist_ok=True)
            with open(networks_path, 'w') as f:
                json.dump(self.networks, f, indent=4)
        except (IOError, OSError) as e:
            # Log error but don't crash - user will notice on next load
            print(f"Warning: Failed to save networks: {e}")

    def connectToNetwork(self):
        """Connect to the selected network."""
        item = self.networkList.currentItem()
        if item:
            nw = next((n for n in self.networks if n['name'] == item.text()), None)
            if nw:
                self.parent.initiate_connection(nw)
                self.accept()

    def editNetwork(self):
        from src.gui.dialogs.network_edit import NetworkEditDialogue
        item = self.networkList.currentItem()
        if not item: return
        nw = next((n for n in self.networks if n['name'] == item.text()), None)
        if nw and NetworkEditDialogue(nw, self).exec_():
            self.save_networks()
            self.refresh_list()

    def addNetwork(self):
        from src.gui.dialogs.network_edit import NetworkEditDialogue
        new_nw = {
            "name": "New Network", "host": "", "port": 6667, "nick": "pyechat_user",
            "realname": "User", "channels": [], "use_ssl": False, "password": ""
        }
        if NetworkEditDialogue(new_nw, self).exec_():
            self.networks.append(new_nw)
            self.save_networks()
            self.refresh_list()

    def refresh_list(self):
        self.networkList.clear()
        for nw in self.networks: self.networkList.addItem(nw['name'])
