"""Main window for PyeChat IRC client."""
import os
import json
import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QTextBrowser, QLabel, QMenu, 
                             QTreeWidget, QTreeWidgetItem, QApplication, 
                             QSplitter, QPlainTextEdit)
from PyQt5.QtGui import QIcon, QTextCursor, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer
from src.irc.irc_client import IRCClient
from src.gui.utils.colors import get_nick_colour
from src.gui.utils.formatters import irc_to_html
from src.gui.dialogs.network_list import NetworkListDialogue
from src.gui.dialogs.settings import SettingsDialogue

DEFAULT_WINDOW_X = 100
DEFAULT_WINDOW_Y = 100
DEFAULT_WINDOW_WIDTH = 1100
DEFAULT_WINDOW_HEIGHT = 700

MESSAGE_BATCH_INTERVAL_MS = 100
NETWORK_LIST_DELAY_MS = 100
MAX_MESSAGES_PER_BATCH = 500

NICK_PREFIXES = ('~', '&', '@', '%', '+')
NICK_RANK_MAP = {'~': 0, '&': 1, '@': 2, '%': 3, '+': 4}
NICK_RANK_MODES = {'o': '@', 'v': '+', 'h': '%', 'a': '&', 'q': '~'}

INPUT_MIN_HEIGHT = 30
INPUT_MAX_HEIGHT = 85
INPUT_PADDING = 12

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_nw = None
        self.current_target = ""
        self.tree_items = {}
        self.clients = {}
        self.buffers = {}
        
        self.load_settings()
        
        self.setObjectName("PyeChat")
        self.setWindowTitle("PyeChat")
        
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'pyechat.png'))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setGeometry(DEFAULT_WINDOW_X, DEFAULT_WINDOW_Y, 
                        DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QHBoxLayout(self.central)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.setup_ui()
        self.setup_menu()
        self.apply_theme()
        
        self.nick_update_queued = set()
        self.nick_timer = QTimer()
        self.nick_timer.setSingleShot(True)
        self.nick_timer.timeout.connect(self.flush_nicks)
        
        self.msg_queue = []
        self.msg_timer = QTimer()
        self.msg_timer.setInterval(MESSAGE_BATCH_INTERVAL_MS)
        self.msg_timer.timeout.connect(self.flush_messages)
        self.msg_timer.start()

        if not self.settings.get("skip_network_list", False):
            QTimer.singleShot(NETWORK_LIST_DELAY_MS, self.openNetworkListDialogue)

    def load_settings(self):
        settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'settings.json'))
        try:
            with open(settings_path, 'r') as f: self.settings = json.load(f)
            for k, v in self.settings.items():
                if v == "#3584E4" or v == "#3584e4": self.settings[k] = "#E95420"
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {
                "show_timestamps": True,
                "ts_format": "[%H:%M:%S]",
                "show_events": True,
                "auto_reconnect": True,
                "nick_colouring": True,
                "highlight_mentions": True,
                "use_system_theme": True,  # Default to system theme - respect OS!
                # Chat Area
                "bg_colour": "#ffffff",
                "fg_colour": "#000000",
                "ts_colour": "#888888",
                "hl_bg": "rgba(255, 204, 0, 0.2)",
                "hl_border": "#ffcc00",
                # Tree/Network List
                "tree_bg": "#f3f3f3",
                "tree_fg": "#000000",
                "tree_sel_bg": "#E95420",
                "tree_sel_fg": "#ffffff",
                # Nick List
                "nick_bg": "#f3f3f3",
                "nick_fg": "#000000",
                "nick_sel_bg": "#E95420",
                "nick_sel_fg": "#ffffff",
                # Topic Bar
                "topic_bg": "#e8e8e8",
                "topic_fg": "#000000",
                "topic_border": "#cccccc",
                # Input Box
                "input_bg": "#ffffff",
                "input_fg": "#000000",
                "input_border": "#cccccc",
                # Menu & Status
                "menu_bg": "#ffffff",
                "menu_fg": "#000000",
                "menu_hover_bg": "#E95420",
                "status_bg": "#f3f3f3",
                "status_fg": "#000000",
                # Borders & Scrollbars
                "border_colour": "#cccccc",
                "scrollbar_bg": "#f3f3f3",
                "scrollbar_handle": "#999999",
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
                    "INVITE": {"fmt": "*** {sender} invited {nick} to {channel}", "colour": "#0000aa"},
                    "ACTION": {"fmt": "* {sender} {msg}", "colour": "#00aa00"}
                }
            }

    def save_settings(self):
        settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'settings.json'))
        try:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except (IOError, OSError) as e:
            print(f"Warning: Failed to save settings: {e}")

    def apply_theme(self):
        s = self.settings
        if s.get("use_system_theme", True):
            app = QApplication.instance()
            if app:
                palette = app.style().standardPalette()
                from PyQt5.QtGui import QPalette, QColor
                palette.setColor(QPalette.Highlight, QColor("#E95420"))
                palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
                app.setPalette(palette)
            
            self.setStyleSheet("""
                QTreeWidget { border: none; outline: none; }
                QTreeWidget::item { padding: 2px; }
                QPlainTextEdit {
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    padding: 3px;
                }
                QPlainTextEdit:focus {
                    border: 2px solid #E95420;
                    padding: 2px;
                }
            """)
            
            if "font" in self.settings:
                f = QFont()
                f.fromString(self.settings["font"])
                self.chat.setFont(f)
            return
        
        self.input.setStyleSheet("")
        
        bg = s.get("bg_colour", "#1e1e1e")
        fg = s.get("fg_colour", "#ffffff")
        
        tree_bg = s.get("tree_bg", s.get("sidebar_bg", "#252526"))
        tree_fg = s.get("tree_fg", s.get("sidebar_fg", "#cccccc"))
        tree_sel_bg = s.get("tree_sel_bg", "#E95420")
        tree_sel_fg = s.get("tree_sel_fg", "#ffffff")
        
        nick_bg = s.get("nick_bg", s.get("sidebar_bg", "#252526"))
        nick_fg = s.get("nick_fg", s.get("sidebar_fg", "#cccccc"))
        nick_sel_bg = s.get("nick_sel_bg", "#E95420")
        nick_sel_fg = s.get("nick_sel_fg", "#ffffff")
        
        t_bg = s.get("topic_bg", "#333333")
        t_fg = s.get("topic_fg", "#ffffff")
        t_border = s.get("topic_border", "#cccccc")
        
        i_bg = s.get("input_bg", "#3c3c3c")
        i_fg = s.get("input_fg", "#ffffff")
        i_border = s.get("input_border", "#cccccc")
        
        menu_bg = s.get("menu_bg", bg)
        menu_fg = s.get("menu_fg", fg)
        menu_hover = s.get("menu_hover_bg", "#E95420")
        
        status_bg = s.get("status_bg", bg)
        status_fg = s.get("status_fg", fg)
        
        border = s.get("border_colour", "#cccccc")
        scroll_bg = s.get("scrollbar_bg", tree_bg)
        scroll_handle = s.get("scrollbar_handle", "#999999")
        
        style = f"""QMainWindow, QDialog {{ background-color: {bg}; color: {fg}; }}
                QMenuBar {{ background-color: {menu_bg}; color: {menu_fg}; border-bottom: 1px solid {border}; }}
                QMenuBar::item {{ background-color: transparent; padding: 4px 10px; margin: 0; }}
                QMenuBar::item:selected {{ background-color: {menu_hover}; color: white; }}
                QMenu {{ background-color: {menu_bg}; color: {menu_fg}; border: 1px solid {border}; padding: 2px; }}
                QMenu::item {{ padding: 3px 28px 3px 6px; border: 1px solid transparent; }}
                QMenu::item:selected {{ background-color: {menu_hover}; color: white; }}
                QMenu::separator {{ height: 1px; background: {border}; margin: 4px 2px; }}
                QPlainTextEdit {{ background-color: {i_bg}; color: {i_fg}; border: 1px solid {i_border}; border-radius: 4px; padding: 2px; font-size: 14px; }}
                QTreeWidget { background-color: {tree_bg}; color: {tree_fg}; border: none; outline: none; }
                QTreeWidget::item { padding: 2px; }
                QTreeWidget::item:selected { background-color: {tree_sel_bg}; color: {tree_sel_fg}; }
                QTreeWidget::branch { width: 12px; }
                QListWidget {{ background-color: {nick_bg}; color: {nick_fg}; border: none; }}
                QListWidget::item:selected {{ background-color: {nick_sel_bg}; color: {nick_sel_fg}; }}
                QLabel#topic {{ background-color: {t_bg}; color: {t_fg}; padding: 4px; border: 1px solid {t_border}; font-weight: normal; margin-bottom: 2px; }}
                QSplitter::handle {{ background-color: {border}; width: 1px; }}
                QStatusBar {{ background-color: {status_bg}; color: {status_fg}; border-top: 1px solid {border}; }}
                QScrollBar:vertical {{ background: {scroll_bg}; width: 12px; }}
                QScrollBar::handle:vertical {{ background: {scroll_handle}; border-radius: 6px; min-height: 20px; }}
                QScrollBar:horizontal {{ background: {scroll_bg}; height: 12px; }}
                QScrollBar::handle:horizontal {{ background: {scroll_handle}; border-radius: 6px; min-width: 20px; }}"""
        
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
            f = QFont()
            f.fromString(self.settings["font"])
            self.chat.setFont(f)

    def setup_ui(self):
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        self.tree = QTreeWidget()
        self.tree.setObjectName("channel_tree")
        self.tree.setHeaderHidden(True)
        self.tree.setFixedWidth(200)
        self.tree.itemClicked.connect(self.on_tree_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_tree_context_menu)
        self.splitter.addWidget(self.tree)

        self.mid_container = QWidget()
        self.mid_layout = QVBoxLayout(self.mid_container)
        self.mid_layout.setContentsMargins(0, 0, 0, 0)
        self.mid_layout.setSpacing(0)
        
        self.topic = QLabel("")
        self.topic.setObjectName("topic")
        self.chat = QTextBrowser()
        self.chat.setReadOnly(True)
        self.chat.setOpenExternalLinks(True)
        
        self.input = QPlainTextEdit()
        self.input.setObjectName("chat_input")
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

        self.nicks = QListWidget()
        self.nicks.setObjectName("nick_list")
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
        doc = self.input.document()
        layout = doc.documentLayout()
        doc.setTextWidth(self.input.viewport().width())
        h = doc.size().height() + INPUT_PADDING
        self.input.setFixedHeight(int(min(max(h, INPUT_MIN_HEIGHT), INPUT_MAX_HEIGHT)))
        
        if h > INPUT_MAX_HEIGHT:
            self.input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def do_tab_completion(self):
        cursor = self.input.textCursor()
        pos = cursor.position()
        text = self.input.toPlainText()
        
        if pos == 0: return
        
        # 1. Check if we're already cycling through candidates
        if hasattr(self, '_tab_state') and self._tab_state['text'] == text and self._tab_state['pos'] == pos:
            state = self._tab_state
            idx = (state['idx'] + 1) % len(state['candidates'])
            state['idx'] = idx
            
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, state['len'])
            new_val = state['candidates'][idx]
            
            comp_suffix = self.settings.get("completion_suffix", ":")
            suffix = (comp_suffix + " ") if state['start'] == 0 else " "
            if not comp_suffix and state['start'] == 0: suffix = " "
            
            cursor.insertText(new_val + suffix)
            
            state['text'] = self.input.toPlainText()
            state['pos'] = cursor.position()
            state['len'] = len(new_val + suffix)
            self.input.setTextCursor(cursor)
            return

        start = pos
        while start > 0 and not text[start-1].isspace():
            start -= 1
        
        word = text[start:pos]
        if not word: return
        word_lower = word.lower()
        
        candidates = []
        seen = set()
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        
        if self.current_nw and self.current_target:
            buf = self.buffers.get((self.current_nw, self.current_target))
            if buf:
                for n in buf.get("nicks", []):
                    raw = n.lstrip(prefix_chars)
                    raw_l = raw.lower()
                    if raw_l.startswith(word_lower) and raw_l not in seen:
                        candidates.append(raw)
                        seen.add(raw_l)
        
        if self.current_nw:
            nw_it = self.find_item(self.current_nw, "")
            if nw_it:
                for i in range(nw_it.childCount()):
                    chan = nw_it.child(i).text(0)
                    chan_l = chan.lower()
                    if chan_l.startswith(word_lower) and chan_l not in seen:
                        candidates.append(chan)
                        seen.add(chan_l)
                        
        if not candidates: return
        candidates.sort(key=lambda x: x.lower())
        
        completed = candidates[0]
        comp_suffix = self.settings.get("completion_suffix", ":")
        suffix = (comp_suffix + " ") if start == 0 else " "
        if not comp_suffix and start == 0: suffix = " "
        
        cursor.setPosition(start, QTextCursor.KeepAnchor)
        cursor.insertText(completed + suffix)
        
        self._tab_state = {
            'text': self.input.toPlainText(),
            'pos': cursor.position(),
            'candidates': candidates,
            'idx': 0,
            'start': start,
            'len': len(completed + suffix)
        }
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
        
        it = QTreeWidgetItem(self.tree)
        it.setText(0, name)
        it.setExpanded(True)
        it.setFont(0, QFont("", -1, QFont.Bold))
        self.tree_items[(name, "")] = it
        
        self.setup_buffer(name, "")
        client = IRCClient(
            name, nw['host'], nw['port'], nw['nick'], nw['realname'], 
            nw.get('channels', []), nw.get('use_ssl', False), nw.get('password'), 
            self.settings.get("auto_reconnect", True),
            nw.get('sasl_method'), nw.get('sasl_user'), nw.get('sasl_pass'),
            nw.get('auto_commands', [])
        )
        self.clients[name] = client
        client.received_message.connect(lambda t, m, tags, n=name: self.on_message(n, t, m, tags))
        client.received_nick_list.connect(lambda d, n=name: self.on_nick(n, d))
        client.received_topic.connect(lambda c, t, n=name: self.on_topic(n, c, t))
        client.parted_channel.connect(lambda c, ni, n=name: self.on_part(n, c, ni))
        client.nick_changed.connect(lambda o, ni, n=name: self.on_nick_change(n, o, ni))
        client.received_kick.connect(lambda c, t, k, r, n=name: self.on_kick(n, c, t, k, r))
        client.received_mode.connect(lambda c, s, m, n=name: self.on_mode(n, c, s, m))
        client.received_invite.connect(lambda c, s, ni, n=name: self.on_invite(n, c, s, ni))
        client.received_action.connect(lambda t, s, m, n=name: self.on_action(n, t, s, m))
        client.received_quit.connect(lambda ni, r, n=name: self.on_quit(n, ni, r))
        client.event_received.connect(lambda c, s, a, t, n=name: self.on_event_received(n, c, s, a, t))
        client.disconnected_from_server.connect(lambda n=name: self.on_disconnect(n))
        self.switch_buffer(name, "")
        client.connect_to_host()

    def setup_buffer(self, nw, target):
        if (nw, target) not in self.buffers: 
            self.buffers[(nw, target)] = {
                "messages": [], "nicks": [], "topic": "",
                "activity": False, "highlight": False
            }

    def switch_buffer(self, nw, target):
        if self.current_nw == nw and self.current_target == target:
            return
        
        self.current_nw, self.current_target = nw, target
        self.setup_buffer(nw, target)
        buf = self.buffers[(nw, target)]
        
        # Reset activity highlights
        buf["activity"] = buf["highlight"] = False
        it = self.find_item(nw, target)
        if it:
            it.setForeground(0, QPalette().color(QPalette.WindowText))
            font = it.font(0)
            if not target: font.setBold(True) # Keep networks bold
            else: font.setBold(False)
            it.setFont(0, font)

        try:
            self.chat.setUpdatesEnabled(False)
            self.chat.clear()
            if buf["messages"]:
                self.chat.setHtml("".join(buf["messages"]))
                self.chat.moveCursor(QTextCursor.End)
        finally:
            self.chat.setUpdatesEnabled(True)
            self.chat.viewport().update()
        
        # Update UI elements
        topic_text = buf["topic"] or target
        if buf["nicks"]:
            topic_text = f"({len(buf['nicks'])}) {topic_text}"
        self.topic.setText(topic_text)
        self.render_nick_list()
        
        # Status Bar Info
        msg = f"<b>NW:</b> {nw}"
        if nw in self.clients:
            msg += f" | <b>Nick:</b> {self.clients[nw].nickname}"
        if target:
            msg += f" | <b>Buf:</b> {target}"
        
        from PyQt5.QtWidgets import QLabel
        if not hasattr(self, 'status_label'):
            self.status_label = QLabel()
            self.statusBar().addWidget(self.status_label)
        self.status_label.setText(msg)

    def on_tree_click(self, item, col):
        p = item.parent()
        if p: self.switch_buffer(p.text(0), item.text(0))
        else: self.switch_buffer(item.text(0), "")
        self.input.setFocus()

    def on_event_received(self, nw, command, sender, args, tags):
        events = self.settings.get("events_v2", {})
        if command not in events: return
        data = events[command]
        fmt = data["fmt"] if isinstance(data, dict) else data
        clr_hex = data.get("colour", "") if isinstance(data, dict) else ""
        if not fmt: return
        
        if command == "MODE":
            mode_str = " ".join(args[1:]) if len(args) > 1 else ""
            chan = args[0] if len(args) > 0 else ""
            
            # Intelligent MODE parsing
            parts = mode_str.split()
            if parts:
                flags = parts[0]
                m_args = parts[1:]
                arg_idx = 0
                parsed_modes = []
                action = "+"
                
                for char in flags:
                    if char in "+-":
                        action = char
                        continue
                    
                    plus_clr = "\x0303" # Green
                    minus_clr = "\x0304" # Red
                    clr = plus_clr if action == "+" else minus_clr
                    
                    if char in NICK_RANK_MODES and arg_idx < len(m_args):
                        target = m_args[arg_idx]
                        arg_idx += 1
                        desc = ""
                        if char == "o": desc = "ops"
                        elif char == "v": desc = "voice"
                        elif char == "h": desc = "half-ops"
                        elif char == "a": desc = "admin"
                        elif char == "q": desc = "owner"
                        
                        verb = "gives" if action == "+" else "removes"
                        prep = "to" if action == "+" else "from"
                        parsed_modes.append(f"{verb} {clr}{desc}\x0f {prep} {target}")
                    elif char in "beIkl": # Modes with args
                        if arg_idx < len(m_args):
                            parsed_modes.append(f"sets mode: {clr}{action}{char}\x0f {m_args[arg_idx]}")
                            arg_idx += 1
                        else:
                            parsed_modes.append(f"sets mode: {clr}{action}{char}\x0f")
                    else:
                        parsed_modes.append(f"sets mode: {clr}{action}{char}\x0f")
                
                if parsed_modes:
                    # If it's just one mode, we can show it nicely
                    if len(parsed_modes) == 1:
                        msg = f"*** {sender} {parsed_modes[0]}"
                    else:
                        msg = f"*** {sender} sets modes: {', '.join(parsed_modes)}"
                    
                    # Ensure color code from settings is passed through tags
                    tags["fmt_color"] = clr_hex
                    self.on_message(nw, chan, msg, tags)
                    return

        ctx = {
            "nick": sender, "sender": sender,
            "channel": args[0] if len(args) > 0 else "",
            "target": args[1] if len(args) > 1 else (args[0] if len(args) > 0 else ""),
            "msg": args[-1] if len(args) > 0 else "",
            "reason": args[-1] if len(args) > 0 else "",
            "mode": " ".join(args[1:]) if len(args) > 1 else "",
            "kicker": sender,
            "old_nick": sender,
            "new_nick": args[0] if len(args) > 0 else "",
            "white": "\x0300", "black": "\x0301", "blue": "\x0302", "green": "\x0303",
            "red": "\x0304", "brown": "\x0305", "purple": "\x0306", "orange": "\x0307",
            "yellow": "\x0308", "teal": "\x0310", "cyan": "\x0311", "light_blue": "\x0312",
            "pink": "\x0313", "grey": "\x0314", "plain": "\x0f"
        }
        
        if command == "KICK" and len(args) > 1:
            ctx["nick"] = args[1]
            ctx["target"] = args[1]
            ctx["reason"] = args[2] if len(args) > 2 else ""
            ctx["msg"] = ctx["reason"]

        try:
            if command == "KICK" and len(args) > 1:
                kicked_nick = args[1]
                if kicked_nick.lower() == self.clients[nw].nickname.lower():
                    channel = args[0] if len(args) > 0 else ""
                    reason = args[2] if len(args) > 2 else ""
                    msg = f"* You have been kicked from {channel} by {sender} ({reason})"
                else:
                    msg = fmt.format(**ctx)
            else:
                msg = fmt.format(**ctx)
                
            tags["fmt_color"] = clr_hex
            target = ctx["channel"]
            if not target.startswith('#'):
                if command in ["NOTICE", "ACTION", "PRIVMSG"]:
                    if target.lower() == self.clients[nw].nickname.lower(): target = sender
                else: target = ""
            
            if command == "JOIN" and sender.lower() == self.clients[nw].nickname.lower():
                self.setup_buffer(nw, target)
                if not self.find_item(nw, target): self.add_tree_item(nw, target)
                if not self.current_target: self.switch_buffer(nw, target)
            
            self.on_message(nw, target, msg, tags)
        except Exception as e:
            # Log formatting errors but don't crash
            print(f"Event formatting error for {command}: {e}")

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
            t_tag = tags.get('time')
            dt = datetime.datetime.fromisoformat(t_tag.replace('Z', '+00:00')) if t_tag else datetime.datetime.now()
            ts = f'<span style="color: {colour};">{dt.strftime(fmt)} </span>'

        # Assemble the final line with highlight styling if needed
        if is_highlight:
            bg = self.settings.get("hl_bg", "rgba(255, 204, 0, 0.1)")
            border = self.settings.get("hl_border", "#ffcc00")
            final_line = f'<div style="background-color: {bg}; border-left: 3px solid {border}; padding-left: 5px;">{ts}{formatted_msg}</div>'
        else:
            style = ""
            if "fmt_color" in tags and tags["fmt_color"]:
                style = f' style="color: {tags["fmt_color"]};"'
            final_line = f'<div{style}>{ts}{formatted_msg}</div>'

        buf = self.buffers[(nw, target)]
        buf["messages"].append(final_line)
        if len(buf["messages"]) > 2500: buf["messages"].pop(0)
        
        if target and not self.find_item(nw, target):
            self.add_tree_item(nw, target)
        
        # Batch messages for UI
        self.msg_queue.append((nw, target, final_line))
        
        # Logging to disk
        if self.settings.get("enable_logging", True):
            log_dir = os.path.join("logs", nw)
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{target or 'status'}.log")
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            clean_msg = msg # Use original msg for clean logs
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} {clean_msg}\n")
            except Exception as e:
                print(f"Logging error: {e}")
        
        # Activity Highlighting in tree
        if nw == self.current_nw and target == self.current_target: return
        
        it = self.find_item(nw, target)
        if it:
            if is_highlight:
                buf["highlight"] = True
                it.setForeground(0, QColor("#E95420")) # Ubuntu Orange
            else:
                buf["activity"] = True
                if not buf["highlight"]:
                    # Use a brighter version of the theme text color for activity
                    # In dark mode this is usually white.
                    it.setForeground(0, QColor("#ffffff" if self.settings.get("bg_colour", "#1e1e1e") != "#ffffff" else "#000000"))
            
            font = it.font(0)
            font.setBold(True)
            it.setFont(0, font)

    def flush_messages(self):
        if not self.msg_queue: return
        batch_size = min(MAX_MESSAGES_PER_BATCH, len(self.msg_queue))
        batch = self.msg_queue[:batch_size]
        self.msg_queue = self.msg_queue[batch_size:]
        
        updates = {}
        for nw, target, line in batch:
            if (nw, target) not in updates: updates[(nw, target)] = []
            updates[(nw, target)].append(line)
            
        if (self.current_nw, self.current_target) in updates:
            bar = self.chat.verticalScrollBar()
            at_bottom = bar.value() >= bar.maximum() - 20
            self.chat.append("".join(updates[(self.current_nw, self.current_target)]))
            if at_bottom: self.chat.moveCursor(QTextCursor.End)

    def find_item(self, nw, target):
        return self.tree_items.get((nw, target))

    def add_tree_item(self, nw, target):
        if not target or (nw, target) in self.tree_items: return
        p = self.find_item(nw, "")
        if not p: return
        
        it = QTreeWidgetItem(p)
        it.setText(0, target)
        self.tree_items[(nw, target)] = it

    def remove_tree_item(self, nw, target):
        it = self.tree_items.pop((nw, target), None)
        if it:
            p = it.parent()
            if p: p.removeChild(it)

    def on_nick(self, nw, data):
        chan, nick = data
        self.setup_buffer(nw, chan)
        if not self.find_item(nw, chan): self.add_tree_item(nw, chan)
        
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        raw_nick = nick.lstrip(prefix_chars)
        nicks_list = self.buffers[(nw, chan)]["nicks"]
        
        found = False
        for i, n in enumerate(nicks_list):
            if n.lstrip(prefix_chars).lower() == raw_nick.lower():
                nicks_list[i] = nick
                found = True
                break
        
        if not found: nicks_list.append(nick)
            
        if self.current_nw == nw and self.current_target == chan:
            self.nick_update_queued.add((nw, chan))
            if not self.nick_timer.isActive(): self.nick_timer.start(100)

    def flush_nicks(self):
        if (self.current_nw, self.current_target) in self.nick_update_queued:
            self.render_nick_list()
        self.nick_update_queued.clear()

    def render_nick_list(self):
        self.nicks.setUpdatesEnabled(False)
        self.nicks.clear()
        
        if not self.current_nw or not self.current_target:
            self.nicks.setUpdatesEnabled(True)
            return
            
        buf = self.buffers.get((self.current_nw, self.current_target))
        if not buf:
            self.nicks.setUpdatesEnabled(True)
            return
        
        def get_rank(n):
            return NICK_RANK_MAP.get(n[0], 5)
        
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        sorted_nicks = sorted(
            buf["nicks"], 
            key=lambda x: (get_rank(x), x.lstrip(prefix_chars).lower())
        )
        
        self.nicks.addItems(sorted_nicks)
        self.nicks.setUpdatesEnabled(True)

    def on_part(self, nw, chan, nick):
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        raw_nick = nick.lstrip(prefix_chars)
        
        if raw_nick.lower() == self.clients[nw].nickname.lower() and chan:
            if self.current_nw == nw and self.current_target == chan:
                self.switch_buffer(nw, "")
            self.remove_tree_item(nw, chan)
        
        keys = [(nw, chan)] if chan else [k for k in self.buffers if k[0] == nw]
        
        refresh_needed = False
        for k in keys:
            nicks_list = self.buffers[k].get("nicks", [])
            for n in list(nicks_list):
                if n.lstrip(prefix_chars).lower() == raw_nick.lower():
                    nicks_list.remove(n)
                    if self.current_nw == nw and self.current_target == k[1]:
                        refresh_needed = True
                    break
        
        if refresh_needed:
            self.nick_update_queued.add((self.current_nw, self.current_target))
            if not self.nick_timer.isActive():
                self.nick_timer.start(100)

    def on_quit(self, nw, nick, reason):
        self.on_part(nw, None, nick)
        msg = f"*** {nick} quit ({reason})"
        for k in [k for k in self.buffers if k[0] == nw and k[1]]:
            self.on_message(nw, k[1], msg)

    def on_nick_change(self, nw, old, new):
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        old_raw = old.lstrip(prefix_chars)
        
        refresh_needed = False
        for k in [k for k in self.buffers if k[0] == nw]:
            nicks_list = self.buffers[k].get("nicks", [])
            for i, n in enumerate(nicks_list):
                if n.lstrip(prefix_chars).lower() == old_raw.lower():
                    prefix = n[:len(n) - len(old_raw)]
                    nicks_list[i] = prefix + new
                    # Show nick change in the buffer where it happened
                    msg = f"*** {old} is now known as {new}"
                    self.on_message(nw, k[1], msg)
                    if self.current_nw == nw and self.current_target == k[1]:
                        refresh_needed = True
                    break
        
        if refresh_needed:
            self.nick_update_queued.add((self.current_nw, self.current_target))
            if not self.nick_timer.isActive():
                self.nick_timer.start(100)

    def on_kick(self, nw, chan, target, kicker, reason):
        self.on_event_received(nw, "KICK", kicker, [chan, target, reason], {})
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        target_raw = target.lstrip(prefix_chars)
        
        if target_raw.lower() == self.clients[nw].nickname.lower():
            if self.current_nw == nw and self.current_target == chan:
                self.switch_buffer(nw, "")
            self.remove_tree_item(nw, chan)
            
        nicks_list = self.buffers.get((nw, chan), {}).get("nicks", [])
        for n in list(nicks_list):
            if n.lstrip(prefix_chars).lower() == target_raw.lower():
                nicks_list.remove(n)
                if self.current_nw == nw and self.current_target == chan:
                    self.nick_update_queued.add((nw, chan))
                    if not self.nick_timer.isActive():
                        self.nick_timer.start(100)
                break

    def on_mode(self, nw, chan, sender, mode):
        """Handle MODE changes for ranks (@, +, etc.)."""
        self.on_event_received(nw, "MODE", sender, [chan, mode], {})
        
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        
        parts = mode.split()
        if len(parts) < 2: return
        flags_str = parts[0]
        args = parts[1:]
        
        if not flags_str.startswith(('+', '-')): return
        
        action = flags_str[0] # + or -
        arg_idx = 0
        for char in flags_str[1:]:
            if char in NICK_RANK_MODES:
                if arg_idx < len(args):
                    target_nick = args[arg_idx]
                    prefix = NICK_RANK_MODES[char]
                    
                    nicks = self.buffers.get((nw, chan), {}).get("nicks", [])
                    for i, n in enumerate(nicks):
                        raw = n.lstrip(prefix_chars)
                        if raw.lower() == target_nick.lower():
                            if action == '+':
                                nicks[i] = prefix + raw
                            else:
                                if n.startswith(prefix):
                                    nicks[i] = raw
                            break
                    arg_idx += 1
            elif char in "beI": # List modes always take arg
                arg_idx += 1
            elif char == "k": # Key always takes arg
                arg_idx += 1
            elif char == "l" and action == "+": # Limit takes arg on +
                arg_idx += 1
            # Other modes like +nt skip args
        
        if self.current_nw == nw and self.current_target == chan:
            self.nick_update_queued.add((nw, chan))
            if not self.nick_timer.isActive():
                self.nick_timer.start(100)

    def on_notice(self, nw, target, sender, msg):
        """Handle NOTICE messages."""
        self.on_event_received(nw, "NOTICE", sender, [target, msg], {})

    def on_invite(self, nw, chan, sender, nick):
        msg = f"*** {sender} invited {nick} to {chan}"
        self.on_message(nw, "", msg)

    def on_action(self, nw, target, sender, msg):
        # Route through event system for consistent formatting
        self.on_event_received(nw, "ACTION", sender, [target, msg], {})

    def on_topic(self, nw, chan, topic):
        self.setup_buffer(nw, chan)
        self.add_tree_item(nw, chan)
        self.buffers[(nw, chan)]["topic"] = topic
        if self.current_nw == nw and self.current_target == chan: self.topic.setText(topic)

    def on_disconnect(self, nw):
        self.on_message(nw, "", f"*** Disconnected from {nw}")
        if self.current_nw == nw:
            self.statusBar().showMessage(f"Disconnected from {nw} - auto-reconnect may be in progress", 5000)

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
        if SettingsDialogue(self, self.settings).exec_():
            self.save_settings()
            self.apply_theme()

    def on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        
        menu = QMenu()
        p = item.parent()
        if not p: # Network
            nw = item.text(0)
            if nw in self.clients:
                discon = menu.addAction("Disconnect")
            else:
                con = menu.addAction("Connect")
                
            action = menu.exec_(self.tree.mapToGlobal(pos))
            if nw in self.clients and action == discon:
                self.clients[nw].socket.disconnectFromHost()
            elif nw not in self.clients and action == con:
                pass
        else: # Channel/Target
            nw, target = p.text(0), item.text(0)
            is_chan = target.startswith(('#', '&'))
            
            if is_chan:
                part = menu.addAction("Part Channel")
            close = menu.addAction("Close")
            
            action = menu.exec_(self.tree.mapToGlobal(pos))
            if is_chan and action == part:
                self.clients[nw].send_command(f"PART {target}")
            elif action == close:
                self.remove_tree_item(nw, target)
                if self.current_nw == nw and self.current_target == target:
                    self.switch_buffer(nw, "")
