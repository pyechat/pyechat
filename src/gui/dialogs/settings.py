"""Settings dialog for PyeChat."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QWidget, QTabWidget, QCheckBox, QLineEdit, QComboBox,
                             QGroupBox, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QDialogButtonBox, QScrollArea,
                             QTextEdit, QColorDialog, QFontDialog, QInputDialog)
from PyQt5.QtGui import QColor, QFont
from src.gui.utils.colors import get_nick_colour

class SettingsDialogue(QDialog):
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.parent, self.settings = parent, current_settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.setup_general_tab()
        self.setup_events_tab()
        self.setup_appearance_tab()
        self.setup_identity_tab()
        
        self.layout.addWidget(self.tabs)
        self.btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        self.btns.button(QDialogButtonBox.Apply).clicked.connect(self.apply_live)
        self.layout.addWidget(self.btns)

    def setup_general_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self.ts = QCheckBox(); self.ts.setChecked(self.settings.get("show_timestamps", True))
        self.ts_fmt = QLineEdit(self.settings.get("ts_format", "[%H:%M:%S]"))
        self.events = QCheckBox(); self.events.setChecked(self.settings.get("show_events", True))
        self.reconnect = QCheckBox(); self.reconnect.setChecked(self.settings.get("auto_reconnect", True))
        self.nick_colour = QCheckBox(); self.nick_colour.setChecked(self.settings.get("nick_colouring", True))
        self.highlight = QCheckBox(); self.highlight.setChecked(self.settings.get("highlight_mentions", True))
        
        self.conn_info = QComboBox()
        self.conn_info.addItems(["Minimal", "Standard", "Verbose"])
        self.conn_info.setCurrentText(self.settings.get("conn_info_level", "Standard"))
        
        self.comp_suffix = QLineEdit(self.settings.get("completion_suffix", ":"))
        self.comp_suffix.setFixedWidth(50)
        
        layout.addRow("Show Timestamps:", self.ts)
        layout.addRow("Timestamp Format:", self.ts_fmt)
        layout.addRow("Show Join/Part/Quit:", self.events)
        layout.addRow("Auto Reconnect:", self.reconnect)
        layout.addRow("Nick Colouring:", self.nick_colour)
        layout.addRow("Highlight Mentions:", self.highlight)
        layout.addRow("Conn. Info Level:", self.conn_info)
        layout.addRow("Completion Suffix:", self.comp_suffix)
        
        self.tabs.addTab(tab, "General")

    def setup_events_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.event_table = QTableWidget(0, 3)
        self.event_table.setHorizontalHeaderLabels(["IRC Command", "Message Format", "Line Colour"])
        self.event_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.event_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        evs = self.settings.get("events_v2", self.get_default_events_v2())
        for cmd, data in evs.items():
            fmt = data if isinstance(data, str) else data.get("fmt", "")
            clr = "" if isinstance(data, str) else data.get("colour", "")
            self.add_table_row(cmd, fmt, clr)
        
        layout.addWidget(self.event_table)
        
        btns = QHBoxLayout()
        add_btn = QPushButton("Add Event"); add_btn.clicked.connect(self.add_new_event)
        del_btn = QPushButton("Remove Selected"); del_btn.clicked.connect(self.remove_event)
        btns.addWidget(add_btn); btns.addWidget(del_btn); btns.addStretch()
        layout.addLayout(btns)
        
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
        
        btn = QPushButton("Default" if not clr else "")
        if clr: btn.setStyleSheet(f"background-color: {clr}; border: 1px solid #555;")
        btn.setProperty("colour", clr)
        btn.clicked.connect(lambda: self.pick_event_colour(btn))
        self.event_table.setCellWidget(row, 2, btn)

    def pick_event_colour(self, btn):
        current = QColor(btn.property("colour") or "#ffffff")
        clr = QColorDialog.getColor(current, self, "Pick event colour", QColorDialog.DontUseNativeDialog)
        if clr.isValid():
            c = clr.name()
            btn.setStyleSheet(f"background-color: {c}; border: 1px solid #555;")
            btn.setProperty("colour", c)
            btn.setText("")

    def add_new_event(self):
        cmd, ok = QInputDialog.getText(self, "Add Event", "IRC Command:")
        if ok and cmd: self.add_table_row(cmd.upper(), "", "")

    def remove_event(self):
        self.event_table.removeRow(self.event_table.currentRow())

    def setup_appearance_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumWidth(280)
        container = QWidget()
        layout = QFormLayout(container)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["System Default", "Custom"])
        self.preset_combo.currentTextChanged.connect(self.on_preset_change)
        layout.addRow("Theme Preset:", self.preset_combo)
        layout.addRow(QLabel(" "))

        self.add_colour_option(layout, "Chat Background", "bg_colour")
        self.add_colour_option(layout, "Chat Text", "fg_colour")
        self.add_colour_option(layout, "Timestamp Colour", "ts_colour")
        self.add_colour_option(layout, "Mention Background", "hl_bg")
        self.add_colour_option(layout, "Mention Border", "hl_border")
        layout.addRow(QLabel(" "))
        
        self.add_colour_option(layout, "Tree Background", "tree_bg")
        self.add_colour_option(layout, "Tree Text", "tree_fg")
        self.add_colour_option(layout, "Tree Selection BG", "tree_sel_bg")
        self.add_colour_option(layout, "Tree Selection Text", "tree_sel_fg")
        layout.addRow(QLabel(" "))
        
        self.add_colour_option(layout, "Nick List Background", "nick_bg")
        self.add_colour_option(layout, "Nick List Text", "nick_fg")
        self.add_colour_option(layout, "Nick Selection BG", "nick_sel_bg")
        self.add_colour_option(layout, "Nick Selection Text", "nick_sel_fg")
        layout.addRow(QLabel(" "))
        
        self.font_btn = QPushButton("Change Chat Font")
        self.font_btn.clicked.connect(self.on_change_font)
        layout.addRow("Font:", self.font_btn)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        preview_group = QGroupBox("Live Theme Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_chat = QTextEdit()
        self.preview_chat.setReadOnly(True)
        self.preview_chat.setHtml(self.get_preview_html())
        preview_layout.addWidget(self.preview_chat)
        main_layout.addWidget(preview_group)

        self.tabs.addTab(tab, "Appearance")

    def get_preview_html(self):
        s = self.settings
        bg, fg = s.get("bg_colour", "#1e1e1e"), s.get("fg_colour", "#ffffff")
        ts, hbg, hb = s.get("ts_colour", "#888"), s.get("hl_bg", "rgba(255,150,0,0.1)"), s.get("hl_border", "#E95420")
        c1, c2 = get_nick_colour("Alice", bg), get_nick_colour("Bob", bg)
        nick = s.get("default_nick", "User")
        
        html = f"<div style='background-color:{bg}; color:{fg}; padding:10px; font-family: monospace;'>"
        html += f"<div><span style='color:{ts}'>[12:00:00]</span> <span style='color:{c1}'>&lt;Alice&gt;</span> Hello!</div>"
        html += f"<div><span style='color:{ts}'>[12:00:05]</span> <span style='color:{c2}'>&lt;Bob&gt;</span> Testing theme...</div>"
        html += f"<div style='background-color:{hbg}; border-left:3px solid {hb}; padding-left:5px;'>"
        html += f"<span style='color:{ts}'>[12:00:10]</span> <span style='color:{c1}'>&lt;Alice&gt;</span> {nick}, check this out!</div>"
        html += "</div>"
        return html

    def add_colour_option(self, layout, label, key):
        btn = QPushButton(label)
        btn.clicked.connect(lambda: self.pick_colour(key, btn))
        self.update_button_swatch(btn, key)
        layout.addRow(btn)

    def update_button_swatch(self, btn, key):
        clr = self.settings.get(key, "#ffffff")
        qclr = QColor(clr if not clr.startswith("rgba") else "transparent")
        fg = "#fff" if qclr.lightness() < 128 else "#000"
        btn.setStyleSheet(f"background-color:{clr}; color:{fg}; border:1px solid #555; height:24px; font-weight:bold;")
        if hasattr(self, 'preview_chat'): self.preview_chat.setHtml(self.get_preview_html())

    def pick_colour(self, key, btn):
        current = QColor(self.settings.get(key, "#ffffff"))
        clr = QColorDialog.getColor(current, self, "Pick color", QColorDialog.DontUseNativeDialog)
        if clr.isValid():
            self.settings[key] = clr.name()
            self.update_button_swatch(btn, key)
            self.preset_combo.setCurrentText("Custom")

    def on_preset_change(self, name):
        self.settings["use_system_theme"] = (name == "System Default")
        if hasattr(self, 'preview_chat'): self.preview_chat.setHtml(self.get_preview_html())

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
        self.update_dict()
        self.parent.apply_theme()

    def update_dict(self):
        self.settings.update({
            "show_timestamps": self.ts.isChecked(),
            "ts_format": self.ts_fmt.text(),
            "show_events": self.events.isChecked(),
            "auto_reconnect": self.reconnect.isChecked(),
            "nick_colouring": self.nick_colour.isChecked(),
            "highlight_mentions": self.highlight.isChecked(),
            "conn_info_level": self.conn_info.currentText(),
            "completion_suffix": self.comp_suffix.text(),
            "events_v2": self.get_table_data_v2(),
            "default_nick": self.default_nick.text(),
            "real_name": self.real_name.text()
        })

    def accept(self):
        self.update_dict()
        super().accept()

    def get_table_data_v2(self):
        data = {}
        for r in range(self.event_table.rowCount()):
            it_cmd, it_fmt = self.event_table.item(r, 0), self.event_table.item(r, 1)
            btn_clr = self.event_table.cellWidget(r, 2)
            if it_cmd and it_fmt and btn_clr:
                c, f = it_cmd.text().strip().upper(), it_fmt.text().strip()
                clr = btn_clr.property("colour")
                if c: data[c] = {"fmt": f, "colour": clr}
        return data
