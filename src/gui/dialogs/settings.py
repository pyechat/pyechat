"""Settings dialogue."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QWidget, QTabWidget, QCheckBox, QLineEdit, QComboBox,
                             QGroupBox, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QDialogButtonBox, QScrollArea,
                             QTextEdit, QColorDialog, QFontDialog, QInputDialog)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
from src.gui.utils.colors import get_nick_colour
from src.gui.utils.themes import THEMES

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
        
        # Join/Part filtering options
        self.hide_join_part = QCheckBox()
        self.hide_join_part.setChecked(self.settings.get("hide_join_part", False))
        self.hide_join_part.setToolTip("Completely hide all join/part/quit messages")
        
        self.smart_filter = QCheckBox()
        self.smart_filter.setChecked(self.settings.get("smart_filter_join_part", True))
        self.smart_filter.setToolTip("Hide join/part for users who haven't spoken recently")
        
        self.filter_seconds = QLineEdit(str(self.settings.get("smart_filter_seconds", 300)))
        self.filter_seconds.setFixedWidth(80)
        self.filter_seconds.setToolTip("Time in seconds to track user activity")

        # Numeric replies display
        self.show_numeric_replies = QCheckBox()
        self.show_numeric_replies.setChecked(self.settings.get("show_numeric_replies", False))
        self.show_numeric_replies.setToolTip("Show numeric server replies (e.g., 366 End of NAMES) in channel windows")
        
        self.conn_info = QComboBox()
        self.conn_info.addItems(["Minimal", "Standard", "Verbose"])
        self.conn_info.setCurrentText(self.settings.get("conn_info_level", "Standard"))
        
        self.comp_suffix = QLineEdit(self.settings.get("completion_suffix", ":"))
        self.comp_suffix.setFixedWidth(50)
        
        layout.addRow("Show Timestamps:", self.ts)
        layout.addRow("Timestamp Format:", self.ts_fmt)
        layout.addRow("Show Join/Part/Quit:", self.events)
        layout.addRow("Hide Join/Part/Quit:", self.hide_join_part)
        layout.addRow("Smart Filter Join/Part:", self.smart_filter)
        layout.addRow("Filter Time (seconds):", self.filter_seconds)
        layout.addRow("Show Numeric Replies in Channel:", self.show_numeric_replies)
        layout.addRow("Auto Reconnect:", self.reconnect)
        layout.addRow("Nick Colouring:", self.nick_colour)
        layout.addRow("Highlight Mentions:", self.highlight)
        layout.addRow("Conn. Info Level:", self.conn_info)
        layout.addRow("Completion Suffix:", self.comp_suffix)
        
        self.tabs.addTab(tab, "General")

    def setup_events_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.event_table = QTableWidget(0, 2)
        self.event_table.setHorizontalHeaderLabels(["Event", "Text"])
        self.event_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.event_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.event_table.itemSelectionChanged.connect(self.update_event_legend)
        
        evs = self.settings.get("events_v2", self.get_default_events_v2())
        human_names = self.get_event_name_map()
        for cmd, data in evs.items():
            name = human_names.get(cmd, cmd)
            fmt = data.get("fmt", "") if isinstance(data, dict) else data
            self.add_text_event_row(name, fmt, cmd)
        
        layout.addWidget(self.event_table)
        
        self.legend_group = QGroupBox("Variable Descriptions")
        legend_layout = QVBoxLayout(self.legend_group)
        self.legend_label = QLabel("Select an event to see variable mappings.")
        self.legend_label.setWordWrap(True)
        self.legend_label.setStyleSheet("color: #666; font-style: italic;")
        legend_layout.addWidget(self.legend_label)
        layout.addWidget(self.legend_group)
        
        btns = QHBoxLayout()
        left_btns = QHBoxLayout()
        save_btn = QPushButton("Save As..."); left_btns.addWidget(save_btn)
        load_btn = QPushButton("Load From..."); left_btns.addWidget(load_btn)
        test_btn = QPushButton("Test All"); left_btns.addWidget(test_btn)
        
        right_btns = QHBoxLayout()
        add_btn = QPushButton("Add Event"); add_btn.clicked.connect(self.add_new_event)
        del_btn = QPushButton("Remove Selected"); del_btn.clicked.connect(self.remove_event)
        right_btns.addWidget(add_btn); right_btns.addWidget(del_btn)
        
        btns.addLayout(left_btns)
        btns.addStretch()
        btns.addLayout(right_btns)
        layout.addLayout(btns)
        
        self.tabs.addTab(tab, "Events")

    def get_event_name_map(self):
        return {
            "JOIN": "Join", "PART": "Part", "QUIT": "Quit", 
            "KICK": "Kick", "NICK": "Nick Change", "MODE": "Mode Change",
            "NOTICE": "Notice", "INVITE": "Invite", "ACTION": "Action",
            "311": "Whois User", "312": "Whois Server", "317": "Whois Idle",
            "319": "Whois Channels", "330": "Whois Account", "307": "Whois Registered",
            "301": "Whois Away", "313": "Whois Operator", "318": "Whois End"
        }

    def get_event_legend_map(self):
        return {
            "JOIN": "$1=Nickname, $2=Channel, $3=Hostmask",
            "PART": "$1=Nickname, $2=Hostmask, $3=Channel, $4=Reason",
            "QUIT": "$1=Nickname, $2=Reason, $3=Hostmask",
            "KICK": "$1=Kicker Nick, $2=Kicked Nick, $3=Channel, $4=Reason",
            "NICK": "$1=Old Nickname, $2=New Nickname",
            "MODE": "$1=Sender, $2=Mode String, $3=Target",
            "NOTICE": "$1=Sender, $2=Message",
            "INVITE": "$1=Channel, $2=Sender",
            "ACTION": "$1=Sender, $2=Message",
            "311": "$1=Nick, $2=User, $3=Host, $4=*, $5=Real Name",
            "312": "$1=Nick, $2=Server, $3=Server Info",
            "317": "$1=Nick, $2=Idle (secs), $3=Signon (timestamp)",
            "319": "$1=Nick, $2=Channel list",
            "330": "$1=Nick, $2=Account Name",
            "307": "$1=Nick, $2=Info Message",
            "301": "$1=Nick, $2=Away Message",
            "313": "$1=Nick, $2=Privileges info",
            "318": "$1=Nick, $2=End Message"
        }

    def update_event_legend(self):
        row = self.event_table.currentRow()
        if row < 0: return
        cmd = self.event_table.item(row, 0).data(Qt.UserRole)
        legend = self.get_event_legend_map().get(cmd, "Custom IRC command event.")
        self.legend_label.setText(legend)

    def get_default_events_v2(self):
        return {
            "JOIN": {"fmt": "%C23*$t$1 ($3%C23) has joined", "colour": ""},
            "PART": {"fmt": "%C23*$t$1 ($2%C23) has left $3 (%C23$4%C23)", "colour": ""},
            "QUIT": {"fmt": "%C23*$t$1 has quit (%C23$2%C23)", "colour": ""},
            "KICK": {"fmt": "%C22*$t$1 has kicked $2 from $3 ($4)", "colour": ""},
            "NICK": {"fmt": "%C28*$t$1 is now known as $2", "colour": ""},
            "MODE": {"fmt": "%C29*$t$1 sets mode: $2", "colour": ""},
            "NOTICE": {"fmt": "-%C29$1%C- $2", "colour": ""},
            "INVITE": {"fmt": "*** $2 invited you to $1", "colour": ""},
            "ACTION": {"fmt": "* $1 $2", "colour": ""},
            "311": {"fmt": "%C14Nickname:%O $1\n%C14Host mask:%O $2@$3\n%C14Real name:%O $5", "colour": ""},
            "312": {"fmt": "%C14Connected to:%O $2 ($3)", "colour": ""},
            "317": {"fmt": "%C14Idle since:%O $2s, %C14signon:%O $3", "colour": ""},
            "319": {"fmt": "%C14Channels:%O $2", "colour": ""},
            "330": {"fmt": "%C14Logged in as:%O $2", "colour": ""},
            "307": {"fmt": "%C14Registered nick:%O $2", "colour": ""},
            "301": {"fmt": "%C14Away message:%O $2", "colour": ""},
            "313": {"fmt": "%C14IRC Operator:%O $2", "colour": ""},
            "378": {"fmt": "%C14Actual host:%O $2", "colour": ""},
            "379": {"fmt": "%C14Modes:%O $2", "colour": ""},
            "671": {"fmt": "%C14Secure connection:%O $2", "colour": ""},
            "318": {"fmt": "%C14End of WHOIS", "colour": ""}
        }

    def add_text_event_row(self, name, fmt, cmd):
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)
        item_name = QTableWidgetItem(name)
        item_name.setData(Qt.UserRole, cmd)
        self.event_table.setItem(row, 0, item_name)
        self.event_table.setItem(row, 1, QTableWidgetItem(fmt))

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
        if ok and cmd: self.add_text_event_row(cmd.upper(), "", cmd.upper())

    def remove_event(self):
        row = self.event_table.currentRow()
        if row >= 0: self.event_table.removeRow(row)

    def setup_appearance_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumWidth(280)
        container = QWidget()
        layout = QFormLayout(container)
        
        self.preset_combo = QComboBox()
        theme_names = ["System Default", "Custom"] + list(THEMES.keys())
        self.preset_combo.addItems(theme_names)
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
        clr = QColorDialog.getColor(current, self, "Pick colour", QColorDialog.DontUseNativeDialog)
        if clr.isValid():
            self.settings[key] = clr.name()
            self.update_button_swatch(btn, key)
            self.preset_combo.setCurrentText("Custom")

    def on_preset_change(self, name):
        self.settings["use_system_theme"] = (name == "System Default")
        
        # Apply theme colors if a preset is selected
        if name in THEMES:
            theme = THEMES[name]
            for key, value in theme.items():
                self.settings[key] = value
                # Update button swatches
                for i in range(self.sender().parent().layout().count()):
                    item = self.sender().parent().layout().itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), QPushButton):
                        btn = item.widget()
                        # Check if button text matches a color key
                        btn_keys = {
                            "Chat Background": "bg_colour",
                            "Chat Text": "fg_colour",
                            "Timestamp Colour": "ts_colour",
                            "Mention Background": "hl_bg",
                            "Mention Border": "hl_border",
                            "Tree Background": "tree_bg",
                            "Tree Text": "tree_fg",
                            "Tree Selection BG": "tree_sel_bg",
                            "Tree Selection Text": "tree_sel_fg",
                            "Nick List Background": "nick_bg",
                            "Nick List Text": "nick_fg",
                            "Nick Selection BG": "nick_sel_bg",
                            "Nick Selection Text": "nick_sel_fg",
                        }
                        btn_text = btn.text()
                        if btn_text in btn_keys:
                            self.update_button_swatch(btn, btn_keys[btn_text])
        
        if hasattr(self, 'preview_chat'): 
            self.preview_chat.setHtml(self.get_preview_html())

    def on_change_font(self):
        font, ok = QFontDialog.getFont(self.parent.chat.font(), self)
        if ok:
            self.settings["font"] = font.toString()
            if hasattr(self, 'preview_chat'):
                self.preview_chat.setFont(font)

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
            "hide_join_part": self.hide_join_part.isChecked(),
            "smart_filter_join_part": self.smart_filter.isChecked(),
            "smart_filter_seconds": int(self.filter_seconds.text()) if self.filter_seconds.text().isdigit() else 300,
            "show_numeric_replies": self.show_numeric_replies.isChecked(),
            "auto_reconnect": self.reconnect.isChecked(),
            "nick_colouring": self.nick_colour.isChecked(),
            "highlight_mentions": self.highlight.isChecked(),
            "conn_info_level": self.conn_info.currentText(),
            "completion_suffix": self.comp_suffix.text(),
            "font": self.settings.get("font", ""),
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
            it_name, it_fmt = self.event_table.item(r, 0), self.event_table.item(r, 1)
            if it_name and it_fmt:
                cmd = it_name.data(Qt.UserRole)
                fmt = it_fmt.text().strip()
                if cmd: data[cmd] = {"fmt": fmt, "colour": ""}
        return data
