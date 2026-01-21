from PyQt5.QtWidgets import QMainWindow, QWidget, QColorDialog, QHBoxLayout, QVBoxLayout, QListWidget, QTextEdit, QLineEdit, QCheckBox, QLabel, QMenuBar, QMenu, QStatusBar, QDialog, QPushButton, QFontDialog, QFormLayout, QDialogButtonBox, QSpinBox, QAction, QTreeWidget, QTreeWidgetItem, QTabWidget, QApplication, QScrollArea, QGroupBox, QComboBox, QFrame, QSplitter, QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QListWidgetItem
from PyQt5.QtGui import QIcon, QTextCursor, QFont, QColor, QTextCharFormat, QPalette
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from src.irc.irc_client import IRCClient
import json
import datetime
import hashlib
import re
import html
import webbrowser

def get_nick_colour(nick, bg_colour_hex="#ffffff"):
    # Generates a consistent but unique colour for a nickname
    hash_val = int(hashlib.md5(nick.encode()).hexdigest(), 16)
    hue = hash_val % 360
    # Determine if we should use light or dark text based on background lightness
    qcolour = QColor(bg_colour_hex)
    is_dark_bg = qcolour.lightness() < 128
    lightness = 70 if is_dark_bg else 40
    return f"hsl({hue}, 70%, {lightness}%)"

def irc_to_html(text):
    # mIRC Colour Map
    colours = {
        "0": "#ffffff", "1": "#000000", "2": "#000080", "3": "#008000",
        "4": "#ff0000", "5": "#800000", "6": "#800080", "7": "#ff8000",
        "8": "#ffff00", "9": "#00ff00", "10": "#008080", "11": "#00ffff",
        "12": "#0000ff", "13": "#ff00ff", "14": "#808080", "15": "#c0c0c0"
    }
    
    # Escape existing HTML
    text = html.escape(text)
    
    # Simple formatting
    text = text.replace('\x02', '</b><b>').replace('\x1D', '</i><i>').replace('\x1F', '</u><u>')
    text = f"<b><i><u>{text}</u></i></b>" # Wrappers for easy closing
    
    def colour_repl(match):
        fg, bg = match.group(1), match.group(3)
        res = "</span>"
        if fg:
            c = colours.get(fg, "#fff")
            res += f'<span style="color:{c}'
            if bg:
                bc = colours.get(bg, "#000")
                res += f';background-color:{bc}'
            res += '">'
        return res

    # \x03 followed by optional fg[,bg]
    text = re.sub(r'\x03(\d{1,2})?(,(\d{1,2}))?', colour_repl, text)
    # \x0F Reset
    text = text.replace('\x0f', '</span><span style="color:inherit;background-color:inherit;font-weight:normal;font-style:normal;text-decoration:none">')
    
    # Clean up empty tags and restore wrappers
    res = f'<span style="white-space: pre-wrap;">{text}</span>'
    # URL auto-linking
    url_pattern = r'(https?://[^\s<>"]+|www\.[^\s<>"]+)'
    res = re.sub(url_pattern, r'<a href="\1" style="color: #3399ff;">\1</a>', res)
    return res

class NetworkListDialogue(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Network List")
        self.setMinimumSize(400, 300)
        self.layout = QVBoxLayout(self)
        self.networkList = QListWidget()
        self.networks = self.load_networks()
        for nw in self.networks: self.networkList.addItem(nw['name'])
        self.layout.addWidget(self.networkList)
        
        self.skip_cb = QCheckBox("Skip Network List on startup")
        self.skip_cb.setChecked(self.parent.settings.get("skip_network_list", False))
        self.skip_cb.toggled.connect(self.on_skip_toggled)
        self.layout.addWidget(self.skip_cb)

        self.btn_layout = QHBoxLayout()
        self.connectBtn = QPushButton("Connect"); self.connectBtn.clicked.connect(self.connectToNetwork)
        self.editBtn = QPushButton("Edit"); self.editBtn.clicked.connect(self.editNetwork)
        self.addBtn = QPushButton("Add"); self.addBtn.clicked.connect(self.addNetwork)
        self.btn_layout.addWidget(self.connectBtn); self.btn_layout.addWidget(self.editBtn); self.btn_layout.addWidget(self.addBtn)
        self.layout.addLayout(self.btn_layout)

    def on_skip_toggled(self, checked):
        self.parent.settings["skip_network_list"] = checked
        self.parent.save_settings()

    def load_networks(self):
        try:
            with open('networks.json', 'r') as f: return json.load(f)
        except: return []

    def save_networks(self):
        try:
            with open('networks.json', 'w') as f: json.dump(self.networks, f, indent=4)
        except: pass

    def connectToNetwork(self):
        item = self.networkList.currentItem()
        if item:
            nw = next((n for n in self.networks if n['name'] == item.text()), None)
            if nw: self.parent.initiate_connection(nw); self.accept()

    def editNetwork(self):
        item = self.networkList.currentItem()
        if item:
            nw = next((n for n in self.networks if n['name'] == item.text()), None)
            if nw:
                dlg = NetworkEditDialogue(nw, self)
                if dlg.exec_(): self.save_networks()

    def addNetwork(self):
        new_nw = {"name": "New Network", "host": "", "port": 6667, "nick": "pyechat_user", "realname": "User", "channels": [], "use_ssl": False, "password": ""}
        dlg = NetworkEditDialogue(new_nw, self)
        if dlg.exec_(): self.networks.append(new_nw); self.save_networks(); self.networkList.addItem(new_nw['name'])

class NetworkEditDialogue(QDialog):
    def __init__(self, nw, parent=None):
        super().__init__(parent)
        self.nw = nw
        self.setWindowTitle(f"Edit {nw['name']}")
        self.layout = QFormLayout(self)
        self.name = QLineEdit(nw['name'])
        self.host = QLineEdit(nw['host'])
        self.port = QSpinBox(); self.port.setRange(1, 65535); self.port.setValue(nw['port'])
        self.nick = QLineEdit(nw['nick'])
        self.realname = QLineEdit(nw['realname'])
        self.channels = QLineEdit(", ".join(nw.get('channels', [])))
        self.ssl = QCheckBox(); self.ssl.setChecked(nw.get('use_ssl', False))
        self.pwd = QLineEdit(nw.get('password', "")); self.pwd.setEchoMode(QLineEdit.Password)
        
        self.sasl_method = QComboBox()
        self.sasl_method.addItems(["None", "PLAIN", "EXTERNAL"])
        self.sasl_method.setCurrentText(nw.get('sasl_method', "None"))
        self.sasl_user = QLineEdit(nw.get('sasl_user', ""))
        self.sasl_pass = QLineEdit(nw.get('sasl_pass', "")); self.sasl_pass.setEchoMode(QLineEdit.Password)
        self.auto_cmds = QTextEdit("\n".join(nw.get('auto_commands', [])))
        self.auto_cmds.setPlaceholderText("One command per line, e.g.\nPRIVMSG NickServ :IDENTIFY password")
        self.auto_cmds.setMaximumHeight(80)

        self.layout.addRow("Name:", self.name); self.layout.addRow("Host:", self.host); self.layout.addRow("Port:", self.port)
        self.layout.addRow("Nick:", self.nick); self.layout.addRow("Real Name:", self.realname)
        self.layout.addRow("Channels:", self.channels); self.layout.addRow("SSL:", self.ssl); self.layout.addRow("Password:", self.pwd)
        self.layout.addRow("SASL Method:", self.sasl_method)
        self.layout.addRow("SASL User:", self.sasl_user)
        self.layout.addRow("SASL Pass:", self.sasl_pass)
        self.layout.addRow("Auto-Commands:", self.auto_cmds)

        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); self.btns.accepted.connect(self.accept); self.btns.rejected.connect(self.reject)
        self.layout.addRow(self.btns)

    def accept(self):
        self.nw.update({
            "name": self.name.text(), "host": self.host.text(), "port": self.port.value(), 
            "nick": self.nick.text(), "realname": self.realname.text(), 
            "channels": [c.strip() for c in self.channels.text().split(',') if c.strip()], 
            "use_ssl": self.ssl.isChecked(), "password": self.pwd.text(),
            "sasl_method": self.sasl_method.currentText() if self.sasl_method.currentText() != "None" else None,
            "sasl_user": self.sasl_user.text(),
            "sasl_pass": self.sasl_pass.text(),
            "auto_commands": [l.strip() for l in self.auto_cmds.toPlainText().split('\n') if l.strip()]
        })
        super().accept()

class SettingsDialogue(QDialog):
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.parent, self.settings = parent, current_settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.setup_general_tab()
        self.setup_events_tab() # Now using a table!
        self.setup_appearance_tab()
        self.setup_identity_tab()
        self.layout.addWidget(self.tabs)
        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        self.btns.accepted.connect(self.accept); self.btns.rejected.connect(self.reject); self.btns.button(QDialogButtonBox.Apply).clicked.connect(self.apply_live)
        self.layout.addWidget(self.btns)

    def setup_general_tab(self):
        tab = QWidget(); layout = QFormLayout(tab)
        self.ts = QCheckBox(); self.ts.setChecked(self.settings.get("show_timestamps", True))
        self.ts_fmt = QLineEdit(self.settings.get("ts_format", "[%H:%M:%S]"))
        self.events = QCheckBox(); self.events.setChecked(self.settings.get("show_events", True))
        self.reconnect = QCheckBox(); self.reconnect.setChecked(self.settings.get("auto_reconnect", True))
        self.nick_colour = QCheckBox(); self.nick_colour.setChecked(self.settings.get("nick_colouring", True))
        self.highlight = QCheckBox(); self.highlight.setChecked(self.settings.get("highlight_mentions", True))
        layout.addRow("Show Timestamps:", self.ts)
        layout.addRow("Timestamp Format:", self.ts_fmt)
        layout.addRow("Show Join/Part/Quit:", self.events)
        layout.addRow("Auto Reconnect:", self.reconnect)
        layout.addRow("Nick Colouring:", self.nick_colour)
        layout.addRow("Highlight Mentions:", self.highlight)
        self.conn_info = QComboBox()
        self.conn_info.addItems(["Minimal", "Standard", "Verbose"])
        self.conn_info.setCurrentText(self.settings.get("conn_info_level", "Standard"))
        layout.addRow("Conn. Info Level:", self.conn_info)
        
        self.tabs.addTab(tab, "General")

    def setup_events_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        
        # Legend
        legend = QGroupBox("Placeholder Legend")
        l_layout = QVBoxLayout(legend)
        l_text = QLabel(
            "<b>Placeholders:</b> {nick}, {channel}, {reason}, {mode}, {msg}, {old_nick}, {new_nick}, {kicker}<br/>"
            "<b>Colours:</b> {white}, {black}, {blue}, {green}, {red}, {brown}, {purple}, {orange}, {yellow}, {teal}, {cyan}, {light_blue}, {pink}, {grey}, {plain}"
        )
        l_text.setWordWrap(True); l_text.setStyleSheet("color: #666; font-size: 11px;")
        l_layout.addWidget(l_text); layout.addWidget(legend)

        # Table
        self.event_table = QTableWidget(0, 3)
        self.event_table.setHorizontalHeaderLabels(["IRC Command", "Message Format", "Line Colour"])
        self.event_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.event_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.event_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Load existing
        evs = self.settings.get("events_v2", self.get_default_events_v2())
        for cmd, data in evs.items():
            fmt = data if isinstance(data, str) else data.get("fmt", "")
            clr = "" if isinstance(data, str) else data.get("colour", "")
            self.add_table_row(cmd, fmt, clr)
        
        layout.addWidget(self.event_table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Event"); add_btn.clicked.connect(self.add_new_event)
        del_btn = QPushButton("Remove Selected"); del_btn.clicked.connect(self.remove_event)
        btn_row.addWidget(add_btn); btn_row.addWidget(del_btn); btn_row.addStretch()
        layout.addLayout(btn_row)
        
        self.tabs.addTab(tab, "Events")

    def get_default_events_v2(self):
        return {
            "JOIN": {"fmt": "*** {nick} joined {channel}", "colour": "#00aa00"},
            "PART": {"fmt": "*** {nick} left {channel}", "colour": "#aa0000"},
            "QUIT": {"fmt": "*** {nick} quit ({reason})", "colour": "#aa0000"},
            "KICK": {"fmt": "*** {nick} was kicked by {kicker} ({reason})", "colour": "#ff0000"},
            "NICK": {"fmt": "*** {old_nick} is now known as {new_nick}", "colour": "#00aaaa"},
            "MODE": {"fmt": "*** {sender} sets mode: {mode}", "colour": "#aa00aa"},
            "NOTICE": {"fmt": "-{sender}- {msg}", "colour": "#aaaa00"},
            "INVITE": {"fmt": "*** {sender} invited {nick} to {channel}", "colour": "#0000aa"}
        }

    def add_table_row(self, cmd, fmt, clr=""):
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)
        self.event_table.setItem(row, 0, QTableWidgetItem(cmd))
        self.event_table.setItem(row, 1, QTableWidgetItem(fmt))
        
        color_btn = QPushButton("Default" if not clr else "")
        if clr: color_btn.setStyleSheet(f"background-color: {clr}; border: 1px solid #555;")
        color_btn.setProperty("colour", clr)
        color_btn.clicked.connect(lambda: self.pick_event_colour(color_btn))
        self.event_table.setCellWidget(row, 2, color_btn)

    def pick_event_colour(self, btn):
        current = QColor(btn.property("colour") or "#ffffff")
        colour = QColorDialog.getColor(current, self, "Pick event colour", QColorDialog.DontUseNativeDialog)
        if colour.isValid():
            c = colour.name()
            btn.setStyleSheet(f"background-color: {c}; border: 1px solid #555;")
            btn.setProperty("colour", c)
            btn.setText("")

    def add_new_event(self):
        cmd, ok = QInputDialog.getText(self, "Add Event", "IRC Command (e.g., TOPIC, 372):")
        if ok and cmd: self.add_table_row(cmd.upper(), "", "")

    def remove_event(self):
        self.event_table.removeRow(self.event_table.currentRow())

    def setup_appearance_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        
        # Left side: Scrollable Options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumWidth(280)
        container = QWidget()
        layout = QFormLayout(container)
        
        # Theme Presets
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Custom", "Dracula", "Nord", "Solarized Dark", "Matrix", "Soft Light", "Oceanic"])
        self.preset_combo.currentTextChanged.connect(self.on_preset_change)
        layout.addRow("Theme Preset:", self.preset_combo)
        layout.addRow(QLabel(" "))

        # Granular Colours
        self.add_colour_option(layout, "Chat Background", "bg_colour")
        self.add_colour_option(layout, "Chat Text", "fg_colour")
        self.add_colour_option(layout, "Timestamp Colour", "ts_colour")
        self.add_colour_option(layout, "Mention Background", "hl_bg")
        self.add_colour_option(layout, "Mention Border", "hl_border")
        layout.addRow(QLabel(" "))
        self.add_colour_option(layout, "Sidebar Background", "sidebar_bg")
        self.add_colour_option(layout, "Sidebar Text", "sidebar_fg")
        layout.addRow(QLabel(" "))
        self.add_colour_option(layout, "Topic Background", "topic_bg")
        self.add_colour_option(layout, "Topic Text", "topic_fg")
        layout.addRow(QLabel(" "))
        self.add_colour_option(layout, "Input Background", "input_bg")
        self.add_colour_option(layout, "Input Text", "input_fg")

        self.font_btn = QPushButton("Change Chat Font")
        self.font_btn.clicked.connect(self.on_change_font)
        layout.addRow("Font:", self.font_btn)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Right side: Live Preview
        preview_group = QGroupBox("Live Theme Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_chat = QTextEdit()
        self.preview_chat.setReadOnly(True)
        self.preview_chat.setHtml(self.get_preview_html())
        preview_layout.addWidget(self.preview_chat)
        main_layout.addWidget(preview_group)

        self.tabs.addTab(tab, "Appearance")

    def get_preview_html(self):
        # Generates a sample chat view for the preview window
        ts_colour = self.settings.get("ts_colour", "#888")
        bg_colour = self.settings.get("bg_colour", "#1e1e1e")
        fg_colour = self.settings.get("fg_colour", "#ffffff")
        hl_bg = self.settings.get("hl_bg", "rgba(255, 204, 0, 0.1)")
        hl_border = self.settings.get("hl_border", "#ffcc00")
        
        c1 = get_nick_colour("Alice", bg_colour)
        c2 = get_nick_colour("Bob", bg_colour)
        
        html = f"<div style='background-color: {bg_colour}; color: {fg_colour}; padding: 10px;'>"
        html += f"<div><span style='color:{ts_colour}'>[12:00:00] </span><span style='color:{c1}'>&lt;Alice&gt;</span> Hello!</div>"
        html += f"<div><span style='color:{ts_colour}'>[12:00:05] </span><span style='color:{c2}'>&lt;Bob&gt;</span> How do these colours look?</div>"
        html += f"<div style='background-color: {hl_bg}; border-left: 3px solid {hl_border}; padding-left: 5px;'>"
        my_nick = self.settings.get("default_nick", "User")
        html += f"<span style='color:{ts_colour}'>[12:00:10] </span><span style='color:{c1}'>&lt;Alice&gt;</span> {my_nick}, check this highlight!</div>"
        html += "</div>"
        return html

    def add_colour_option(self, layout, label, key):
        btn = QPushButton(label)
        btn.clicked.connect(lambda: self.pick_colour(key, btn))
        self.update_button_swatch(btn, key)
        layout.addRow(btn)

    def update_button_swatch(self, btn, key):
        colour = self.settings.get(key, "#ffffff")
        qcolour = QColor(colour if not colour.startswith("rgba") else "transparent")
        fg = "#fff" if qcolour.lightness() < 128 else "#000"
        btn.setStyleSheet(f"background-color: {colour}; color: {fg}; border: 1px solid #555; height: 24px; font-weight: bold;")
        if hasattr(self, 'preview_chat'):
            self.preview_chat.setHtml(self.get_preview_html())

    def pick_colour(self, key, btn):
        current = QColor(self.settings.get(key, "#ffffff"))
        # Force the draggable colour map (Non-native Dialogue)
        colour = QColorDialog.getColor(current, self, "Pick an exact colour", QColorDialog.DontUseNativeDialog)
        if colour.isValid():
            self.settings[key] = colour.name()
            self.update_button_swatch(btn, key)
            self.preset_combo.setCurrentText("Custom")

    def on_preset_change(self, name):
        presets = {
            "Dracula": {"bg_colour": "#282a36", "fg_colour": "#f8f8f2", "ts_colour": "#6272a4", "sidebar_bg": "#21222c", "sidebar_fg": "#f8f8f2", "topic_bg": "#44475a", "topic_fg": "#bd93f9", "input_bg": "#282a36", "input_fg": "#f8f8f2", "hl_bg": "rgba(255, 121, 198, 0.1)", "hl_border": "#ff79c6"},
            "Nord": {"bg_colour": "#2e3440", "fg_colour": "#eceff4", "ts_colour": "#4c566a", "sidebar_bg": "#242933", "sidebar_fg": "#d8dee9", "topic_bg": "#3b4252", "topic_fg": "#88c0d0", "input_bg": "#3b4252", "input_fg": "#eceff4", "hl_bg": "rgba(136, 192, 208, 0.1)", "hl_border": "#88c0d0"},
            "Solarized Dark": {"bg_colour": "#002b36", "fg_colour": "#839496", "ts_colour": "#586e75", "sidebar_bg": "#073642", "sidebar_fg": "#93a1a1", "topic_bg": "#073642", "topic_fg": "#211a76", "input_bg": "#002b36", "input_fg": "#839496", "hl_bg": "rgba(181, 137, 0, 0.1)", "hl_border": "#b58900"},
            "Matrix": {"bg_colour": "#000000", "fg_colour": "#00ff00", "ts_colour": "#008800", "sidebar_bg": "#000000", "sidebar_fg": "#00ff00", "topic_bg": "#001100", "topic_fg": "#00ff00", "input_bg": "#000000", "input_fg": "#00ff00", "hl_bg": "rgba(0, 255, 0, 0.1)", "hl_border": "#00ff00"}
        }
        if name in presets:
            self.settings.update(presets[name])
            # Update all buttons
            for i in range(self.tabs.count()):
                scroll = self.tabs.widget(i).findChild(QScrollArea)
                if scroll:
                    container = scroll.widget()
                    for btn in container.findChildren(QPushButton):
                        # Find key corresponding to btn text
                        # This is a bit hacky, normally we'd store refs
                        pass
            self.preview_chat.setHtml(self.get_preview_html())
            # For now just reload the tab view by redrawing buttons (easier to just accept preset)
            # Actually, let's just update the dict and let user see preview

    def on_change_font(self):
        font, ok = QFontDialog.getFont(self.parent.chat.font(), self)
        if ok: self.settings["font"] = font.toString()

    def setup_identity_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        self.default_nick = QLineEdit(self.settings.get("default_nick", "pyechat_user"))
        self.real_name = QLineEdit(self.settings.get("real_name", "PyeChat User"))
        layout.addRow("Default Nick:", self.default_nick)
        layout.addRow("Real Name:", self.real_name)
        self.tabs.addTab(tab, "Identity")

    def apply_live(self):
        self.update_dict(); self.parent.apply_theme()

    def update_dict(self):
        # We don't need to update colour settings here as they are updated directly in pick_colour
        self.settings.update({
            "show_timestamps": self.ts.isChecked(),
            "ts_format": self.ts_fmt.text(),
            "show_events": self.events.isChecked(),
            "auto_reconnect": self.reconnect.isChecked(),
            "nick_colouring": self.nick_colour.isChecked(),
            "highlight_mentions": self.highlight.isChecked(),
            "conn_info_level": self.conn_info.currentText(),
            "events_v2": self.get_table_data_v2(),
            "default_nick": self.default_nick.text(),
            "real_name": self.real_name.text()
        })

    def accept(self):
        self.update_dict(); super().accept()

    def get_table_data_v2(self):
        data = {}
        for r in range(self.event_table.rowCount()):
            it_cmd = self.event_table.item(r, 0)
            it_fmt = self.event_table.item(r, 1)
            btn_clr = self.event_table.cellWidget(r, 2)
            if it_cmd and it_fmt and btn_clr:
                c, f = it_cmd.text().strip().upper(), it_fmt.text().strip()
                clr = btn_clr.property("colour")
                if c: data[c] = {"fmt": f, "colour": clr}
        return data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.clients, self.buffers, self.current_nw, self.current_target = {}, {}, None, ""
        self.load_settings()
        self.setObjectName("PyeChat"); self.setWindowTitle("PyeChat")
        self.setWindowIcon(QIcon('/home/colby/projects/pyechat/pyechat.ico'))
        self.setGeometry(100, 100, 1100, 700)
        self.central = QWidget(); self.setCentralWidget(self.central); self.layout = QHBoxLayout(self.central)
        self.layout.setContentsMargins(0, 0, 0, 0); self.layout.setSpacing(0)
        self.setup_ui(); self.setup_menu(); self.apply_theme()
        
        # Spam Fortress: Batch Update Timers
        self.nick_update_queued = set()
        self.nick_timer = QTimer(); self.nick_timer.setSingleShot(True)
        self.nick_timer.timeout.connect(self.flush_nicks)
        
        self.msg_queue = []
        self.msg_timer = QTimer(); self.msg_timer.setInterval(100)
        self.msg_timer.timeout.connect(self.flush_messages)
        self.msg_timer.start()

        if not self.settings.get("skip_network_list", False):
            QTimer.singleShot(100, self.openNetworkListDialogue)

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f: self.settings = json.load(f)
        except:
            self.settings = {
                "show_timestamps": True,
                "ts_format": "[%H:%M:%S]",
                "show_events": True,
                "auto_reconnect": True,
                "nick_colouring": True,
                "highlight_mentions": True,
                "bg_colour": "#ffffff",
                "fg_colour": "#000000",
                "ts_colour": "#888888",
                "sidebar_bg": "#f3f3f3",
                "sidebar_fg": "#000000",
                "topic_bg": "#e8e8e8",
                "topic_fg": "#000000",
                "input_bg": "#ffffff",
                "input_fg": "#000000",
                "hl_bg": "rgba(255, 204, 0, 0.2)",
                "hl_border": "#ffcc00",
                "default_nick": "pyechat_user",
                "real_name": "PyeChat User",
                "skip_network_list": False,
                "conn_info_level": "Standard",
                "events_v2": {
                    "JOIN": {"fmt": "*** {nick} joined {channel}", "colour": "#00aa00"},
                    "PART": {"fmt": "*** {nick} left {channel}", "colour": "#aa0000"},
                    "QUIT": {"fmt": "*** {nick} quit ({reason})", "colour": "#aa0000"},
                    "KICK": {"fmt": "*** {nick} was kicked by {kicker} ({reason})", "colour": "#ff0000"},
                    "NICK": {"fmt": "*** {old_nick} is now known as {new_nick}", "colour": "#00aaaa"},
                    "MODE": {"fmt": "*** {sender} sets mode: {mode}", "colour": "#aa00aa"},
                    "NOTICE": {"fmt": "-{sender}- {msg}", "colour": "#aaaa00"},
                    "INVITE": {"fmt": "*** {sender} invited {nick} to {channel}", "colour": "#0000aa"}
                }
            }

    def save_settings(self):
        with open('settings.json', 'w') as f: json.dump(self.settings, f)

    def apply_theme(self):
        s = self.settings
        bg, fg = s.get("bg_colour", "#1e1e1e"), s.get("fg_colour", "#ffffff")
        s_bg, s_fg = s.get("sidebar_bg", "#252526"), s.get("sidebar_fg", "#cccccc")
        t_bg, t_fg = s.get("topic_bg", "#333333"), s.get("topic_fg", "#ffffff")
        i_bg, i_fg = s.get("input_bg", "#3c3c3c"), s.get("input_fg", "#ffffff")
        
        style = f"QMainWindow, QDialog {{ background-color: {bg}; color: {fg}; }}" \
                f"QMenuBar {{ background-color: {bg}; color: {fg}; border-bottom: 1px solid #ccc; }}" \
                f"QMenuBar::item {{ background-color: transparent; padding: 4px 10px; margin: 0; }}" \
                f"QMenuBar::item:selected {{ background-color: #3584e4; color: white; }}" \
                f"QMenu {{ background-color: {bg}; color: {fg}; border: 1px solid #999; padding: 2px; }}" \
                f"QMenu::item {{ padding: 3px 28px 3px 6px; border: 1px solid transparent; }}" \
                f"QMenu::item:selected {{ background-color: #3584e4; color: white; }}" \
                f"QMenu::separator {{ height: 1px; background: #ccc; margin: 4px 2px; }}" \
                f"QPlainTextEdit {{ background-color: {i_bg}; color: {i_fg}; border: 1px solid #ccc; border-radius: 4px; padding: 2px; font-size: 14px; }}" \
                f"QTreeWidget, QListWidget {{ background-color: {s_bg}; color: {s_fg}; border: none; }}" \
                f"QLabel#topic {{ background-color: white; color: black; padding: 4px; border: 1px solid #ccc; font-weight: normal; margin-bottom: 2px; }}" \
                f"QSplitter::handle {{ background-color: #ccc; width: 1px; }}" \
                f"QStatusBar {{ background-color: {bg}; color: {fg}; border-top: 1px solid #ccc; }}" \
                f"QScrollBar:vertical {{ background: {s_bg}; width: 12px; }}" \
                f"QScrollBar::handle:vertical {{ background: #ccc; border-radius: 6px; min-height: 20px; }}"
        
        self.setStyleSheet(style)
        self.topic.setObjectName("topic")
        
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(bg))
        palette.setColor(QPalette.WindowText, QColor(fg))
        palette.setColor(QPalette.Base, QColor(bg))
        palette.setColor(QPalette.Text, QColor(fg))
        palette.setColor(QPalette.Button, QColor(i_bg))
        palette.setColor(QPalette.ButtonText, QColor(i_fg))
        self.setPalette(palette)
        if "font" in self.settings:
            f = QFont(); f.fromString(self.settings["font"]); self.chat.setFont(f)

    def setup_ui(self):
        # 1. Splitter for resizable panes
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        # Sidebar
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFixedWidth(200)
        self.tree.itemClicked.connect(self.on_tree_click)
        self.splitter.addWidget(self.tree)

        # Mid Section (Topic, Chat, Input)
        self.mid_container = QWidget()
        self.mid_layout = QVBoxLayout(self.mid_container)
        self.mid_layout.setContentsMargins(0, 0, 0, 0)
        self.mid_layout.setSpacing(0)
        
        self.topic = QLabel("")
        self.topic.setObjectName("topic")
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Message...")
        self.input.setFixedHeight(30)
        self.input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input.textChanged.connect(self.adjust_input_height)
        self.input.installEventFilter(self)
        
        self.input_layout = QVBoxLayout()
        self.input_layout.setContentsMargins(5, 5, 5, 5)
        self.input_layout.addWidget(self.input)
        
        self.mid_layout.addWidget(self.topic)
        self.mid_layout.addWidget(self.chat)
        self.mid_layout.addLayout(self.input_layout)
        self.splitter.addWidget(self.mid_container)

        # Nicklist
        self.nicks = QListWidget()
        self.nicks.setFixedWidth(160)
        self.nicks.setContextMenuPolicy(Qt.CustomContextMenu)
        self.nicks.customContextMenuRequested.connect(self.on_nick_context_menu)
        self.splitter.addWidget(self.nicks)

        self.layout.addWidget(self.splitter)

    def eventFilter(self, obj, event):
        if obj == self.input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Tab:
                self.do_tab_completion()
                return True
            if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                if event.modifiers() & Qt.ShiftModifier:
                    return False # Allow Shift+Enter for newline
                self.on_send()
                return True
        return super().eventFilter(obj, event)

    def adjust_input_height(self):
        # Calculate height based on line count and font metrics
        doc = self.input.document()
        layout = doc.documentLayout()
        
        # This force-refreshes the layout to get the correct height for wrapped text
        doc.setTextWidth(self.input.viewport().width())
        h = doc.size().height() + 12 # 12px for top/bottom padding
        
        limit = 85 # Approx 4 lines
        self.input.setFixedHeight(int(min(max(h, 30), limit)))
        
        # Show scrollbar only if we've hit the limit
        if h > limit:
            self.input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def do_tab_completion(self):
        text = self.input.toPlainText()
        if not text: return
        parts = text.split()
        if not parts: return
        last_word = parts[-1].lower()
        candidates = []
        if self.current_nw and self.current_target:
            candidates = [n for n in self.buffers[(self.current_nw, self.current_target)]["nicks"] if n.lower().startswith(last_word)]
        if not candidates: return
        # Simple completion: just pick the first one
        completed = candidates[0]
        if len(parts) == 1: completed += ": "
        else: completed += " "
        parts[-1] = completed
        self.input.setPlainText(" ".join(parts))
        # Move cursor to end
        cursor = self.input.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.input.setTextCursor(cursor)

    def on_nick_context_menu(self, pos):
        item = self.nicks.itemAt(pos)
        if not item: return
        nick = item.text()
        menu = QMenu()
        whois = menu.addAction("Whois")
        query = menu.addAction("Query (PM)")
        action = menu.exec_(self.nicks.mapToGlobal(pos))
        if action == whois: self.clients[self.current_nw].send_command(f"WHOIS {nick}")
        elif action == query: self.on_message(self.current_nw, nick, "*** Query started")

    def setup_menu(self):
        menu = self.menuBar()
        file = menu.addMenu("PyeChat")
        
        file.addAction("Network List", self.openNetworkListDialogue)
        file.addAction("Settings", self.openSettingsDialogue)
        file.addSeparator()
        file.addAction("Exit", self.close)

    def initiate_connection(self, nw):
        name = nw['name']
        if name in self.clients: return
        item = QTreeWidgetItem(self.tree); item.setText(0, name); item.setExpanded(True); self.tree.addTopLevelItem(item)
        self.setup_buffer(name, "")
        client = IRCClient(
            name, nw['host'], nw['port'], nw['nick'], nw['realname'], 
            nw.get('channels', []), nw.get('use_ssl', False), nw.get('password'), 
            self.settings.get("auto_reconnect", True),
            nw.get('sasl_method'), nw.get('sasl_user'), nw.get('sasl_pass'),
            nw.get('auto_commands', [])
        )
        self.clients[name] = client
        client.received_message.connect(lambda t, m, tags: self.on_message(name, t, m, tags))
        client.received_nick_list.connect(lambda d: self.on_nick(name, d))
        client.received_topic.connect(lambda c, t: self.on_topic(name, c, t))
        client.parted_channel.connect(lambda c, n: self.on_part(name, c, n))
        client.nick_changed.connect(lambda o, n: self.on_nick_change(name, o, n))
        client.received_kick.connect(lambda c, t, k, r: self.on_kick(name, c, t, k, r))
        client.received_mode.connect(lambda c, s, m: self.on_mode(name, c, s, m))
        client.received_invite.connect(lambda c, s, n: self.on_invite(name, c, s, n))
        client.event_received.connect(lambda c, s, a, t: self.on_event_received(name, c, s, a, t))
        client.disconnected_from_server.connect(self.on_disconnect)
        self.switch_buffer(name, ""); client.connect_to_host()

    def setup_buffer(self, nw, target):
        if (nw, target) not in self.buffers: 
            self.buffers[(nw, target)] = {"messages": [], "nicks": [], "topic": ""}

    def switch_buffer(self, nw, target):
        self.current_nw, self.current_target = nw, target
        self.setup_buffer(nw, target)
        buf = self.buffers[(nw, target)]
        
        self.chat.clear()
        # Render batch for performance
        self.chat.setHtml("".join(buf["messages"]))
        self.chat.moveCursor(QTextCursor.End)
        
        self.topic.setText(buf["topic"] or target)
        self.render_nick_list()

    def on_tree_click(self, item, col):
        p = item.parent()
        if p: self.switch_buffer(p.text(0), item.text(0))
        else: self.switch_buffer(item.text(0), "")

    def on_event_received(self, nw, command, sender, args, tags):
        # The heart of the dynamic event system!
        events = self.settings.get("events_v2", {})
        if command not in events: return
        data = events[command]
        fmt = data["fmt"] if isinstance(data, dict) else data
        clr = data.get("colour", "") if isinstance(data, dict) else ""
        if not fmt: return
        
        # Build context for formatting
        ctx = {
            "nick": sender, "sender": sender,
            "channel": args[0] if len(args) > 0 else "",
            "target": args[0] if len(args) > 0 else "",
            "msg": args[-1] if len(args) > 0 else "",
            "reason": args[-1] if len(args) > 0 else "",
            "mode": " ".join(args[1:]) if len(args) > 1 else "",
            "kicker": sender,
            "old_nick": sender,
            "new_nick": args[0] if len(args) > 0 else "",
            # Simplified Colour tags
            "white": "\x0300", "black": "\x0301", "blue": "\x0302", "green": "\x0303",
            "red": "\x0304", "brown": "\x0305", "purple": "\x0306", "orange": "\x0307",
            "yellow": "\x0308", "teal": "\x0310", "cyan": "\x0311", "light_blue": "\x0312",
            "pink": "\x0313", "grey": "\x0314", "plain": "\x0f"
        }
        
        try:
            msg = fmt.format(**ctx)
            if clr:
                msg = f'<span style="color: {clr};">{msg}</span>'
            # Route to correct buffer
            target = ctx["channel"] if ctx["channel"].startswith('#') else ""
            
            # Logic: If I am the one joining/parting, we might want special handling
            if command == "JOIN" and sender.lower() == self.clients[nw].nickname.lower():
                self.setup_buffer(nw, target)
                if not self.find_item(nw, target): self.add_tree_item(nw, target)
                # Only switch if we are currently on the status window (no active channel)
                # or if this is the first channel joining.
                if not self.current_target:
                    self.switch_buffer(nw, target)
            
            self.on_message(nw, target, msg, tags)
        except: pass

    def on_message(self, nw, target, msg, tags=None):
        if tags is None: tags = {}
        
        # Connection Info Filtering
        if "[" in msg and "]" in msg and msg[1:4].isdigit():
            code = msg[1:4]
            level = self.settings.get("conn_info_level", "Standard")
            if level == "Minimal" and code != "001": return
            if level == "Standard" and code not in ["001", "372", "375", "376"]:
                if not (400 <= int(code) <= 599): return

        if "***" in msg and not self.settings.get("show_events", True): return
        
        self.setup_buffer(nw, target)
        
        # Nick Coloring and Highlighting
        formatted_msg = msg
        is_highlight = False
        if msg.startswith('<') and '>' in msg:
            sender = msg[1:msg.find('>')]
            content = msg[msg.find('>')+1:]
            if self.settings.get("nick_colouring", True):
                colour = get_nick_colour(sender, self.settings.get("bg_colour", "#ffffff"))
                formatted_msg = f'<span style="color: {colour}; font-weight: bold;">&lt;{sender}&gt;</span> {irc_to_html(content)}'
            else:
                formatted_msg = f'&lt;{sender}&gt; {irc_to_html(content)}'
            
            if self.settings.get("highlight_mentions", True) and self.clients[nw].nickname.lower() in msg.lower():
                is_highlight = True
        else:
            formatted_msg = irc_to_html(msg)

        # Timestamps
        ts = ""
        if self.settings.get("show_timestamps", True):
            fmt = self.settings.get("ts_format", "[%H:%M:%S]")
            colour = self.settings.get("ts_colour", "#888")
            dt = datetime.datetime.fromisoformat(tags['time'].replace('Z', '+00:00')) if 'time' in tags else datetime.datetime.now()
            ts = f'<span style="color: {colour};">{dt.strftime(fmt)} </span>'

        buf = self.buffers[(nw, target)]
        buf["messages"].append(final_line)
        if len(buf["messages"]) > 2500: buf["messages"].pop(0)
        
        if target and not self.find_item(nw, target): self.add_tree_item(nw, target)
        
        # Batch messages for UI
        self.msg_queue.append((nw, target, final_line))

    def flush_messages(self):
        if not self.msg_queue: return
        
        # Process current batch
        batch = self.msg_queue[:]
        self.msg_queue = []
        
        updates = {}
        for nw, target, line in batch:
            if (nw, target) not in updates: updates[(nw, target)] = []
            updates[(nw, target)].append(line)
            
        # If the currently visible buffer is in the batch, update the UI
        if (self.current_nw, self.current_target) in updates:
            bar = self.chat.verticalScrollBar()
            at_bottom = bar.value() >= bar.maximum() - 20
            
            # Combine batch into one update to reduce layout recalculations
            self.chat.append("".join(updates[(self.current_nw, self.current_target)]))
            
            if at_bottom:
                self.chat.moveCursor(QTextCursor.End)

    def find_item(self, nw, target):
        for i in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(i)
            if it.text(0) == nw:
                for j in range(it.childCount()):
                    if it.child(j).text(0) == target: return it.child(j)
        return None

    def add_tree_item(self, nw, target):
        for i in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(i)
            if it.text(0) == nw:
                child = QTreeWidgetItem(it); child.setText(0, target); return

    def on_nick(self, nw, data):
        chan, nick = data; self.setup_buffer(nw, chan)
        if not self.find_item(nw, chan): self.add_tree_item(nw, chan)
        
        # Clean up existing entry if it's there (to update prefix)
        for i in range(self.nicks.count()):
            if self.nicks.item(i).text().lstrip('~&@%+ ') == nick.lstrip('~&@%+ '):
                self.nicks.takeItem(i); break

        if nick not in self.buffers[(nw, chan)]["nicks"]:
            self.buffers[(nw, chan)]["nicks"].append(nick)
            if self.current_nw == nw and self.current_target == chan:
                # Queue for throttled refresh
                self.nick_update_queued.add((nw, chan))
                if not self.nick_timer.isActive(): self.nick_timer.start(100)

    def flush_nicks(self):
        # Refresh the visible nick list if it was updated
        if (self.current_nw, self.current_target) in self.nick_update_queued:
            self.nick_update_queued.remove((self.current_nw, self.current_target))
            self.render_nick_list()
        self.nick_update_queued.clear()

    def render_nick_list(self):
        if not self.current_nw or not self.current_target: return
        buf = self.buffers.get((self.current_nw, self.current_target))
        if not buf: return
        
        # Sort logic
        def prefix_val(n):
            p = n[0]
            if p == '~': return 0
            if p == '&': return 1
            if p == '@': return 2
            if p == '%': return 3
            if p == '+': return 4
            return 5
        
        sorted_nicks = sorted(buf["nicks"], key=lambda x: (prefix_val(x), x.lstrip('~&@%+ ').lower()))
        
        self.nicks.clear()
        self.nicks.addItems(sorted_nicks)

    def on_part(self, nw, chan, nick):
        keys = [(nw, chan)] if chan else [k for k in self.buffers if k[0] == nw]
        for k in keys:
            if nick in self.buffers[k]["nicks"]:
                self.buffers[k]["nicks"].remove(nick)
                if self.current_nw == nw and self.current_target == k[1]:
                    for i in range(self.nicks.count()):
                        if self.nicks.item(i).text() == nick: self.nicks.takeItem(i); break

    def on_nick_change(self, nw, old, new):
        for k in [k for k in self.buffers if k[0] == nw]:
            if old in self.buffers[k]["nicks"]:
                self.buffers[k]["nicks"].remove(old); self.buffers[k]["nicks"].append(new)
                if self.current_nw == nw and self.current_target == k[1]:
                    for i in range(self.nicks.count()):
                        if self.nicks.item(i).text() == old: self.nicks.item(i).setText(new); self.nicks.sortItems(); break

    def on_kick(self, nw, chan, target, kicker, reason):
        if target in self.buffers.get((nw, chan), {}).get("nicks", []):
            self.buffers[(nw, chan)]["nicks"].remove(target)
            if self.current_nw == nw and self.current_target == chan:
                self.nick_update_queued.add((nw, chan))
                if not self.nick_timer.isActive(): self.nick_timer.start(100)

    def on_mode(self, nw, chan, sender, mode):
        pass

    def on_notice(self, nw, target, sender, msg):
        pass

    def on_invite(self, nw, chan, sender, nick):
        pass

    def on_topic(self, nw, chan, topic):
        self.setup_buffer(nw, chan)
        if not self.find_item(nw, chan): self.add_tree_item(nw, chan)
        self.buffers[(nw, chan)]["topic"] = topic
        if self.current_nw == nw and self.current_target == chan: self.topic.setText(topic)

    def on_disconnect(self, nw):
        self.on_message(nw, "", f"*** Disconnected from {nw}")

    def on_send(self):
        txt = self.input.toPlainText().strip()
        if not txt or not self.current_nw or self.current_nw not in self.clients: return
        c = self.clients[self.current_nw]
        
        if txt.startswith('/'):
            parts = txt[1:].split(' ', 1)
            cmd = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd in ["RAW", "QUOTE"]:
                if args: c.send_command(args)
            elif cmd == "JOIN":
                if args: c.send_command(f"JOIN {args}")
            elif cmd in ["MSG", "QUERY"]:
                m_parts = args.split(' ', 1)
                if len(m_parts) == 2:
                    target, msg = m_parts
                    c.send_command(f"PRIVMSG {target} :{msg}")
                    self.on_message(self.current_nw, target, f"<{c.nickname}> {msg}")
            elif cmd == "ME":
                if self.current_target and args:
                    c.send_command(f"PRIVMSG {self.current_target} :\x01ACTION {args}\x01")
                    self.on_message(self.current_nw, self.current_target, f"* {c.nickname} {args}")
            elif cmd == "NICK":
                if args: c.send_command(f"NICK {args}")
            elif cmd == "PART":
                target = args.split()[0] if args else self.current_target
                if target: c.send_command(f"PART {target}")
            elif cmd == "QUIT":
                c.send_command(f"QUIT :{args}")
            else:
                # Fallback for other /commands (e.g. /WHOIS, /MODE)
                c.send_command(txt[1:])
        elif self.current_target:
            c.send_command(f"PRIVMSG {self.current_target} :{txt}")
            self.on_message(self.current_nw, self.current_target, f"<{c.nickname}> {txt}", {})
            
        self.input.clear()
        self.input.setFixedHeight(30)

    def openNetworkListDialogue(self): NetworkListDialogue(self).exec_()
    def openSettingsDialogue(self):
        if SettingsDialogue(self, self.settings).exec_(): self.save_settings(); self.apply_theme()
