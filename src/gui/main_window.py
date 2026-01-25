"""Main window for PyeChat."""
import os
import json
import datetime
import subprocess
import shlex
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QListWidgetItem, QTextBrowser, QLabel, QMenu, 
                             QTreeWidget, QTreeWidgetItem, QApplication, 
                             QSplitter, QSizePolicy)
from PyQt5.QtGui import QIcon, QTextCursor, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer

from src.irc.irc_client import IRCClient
from src.gui.utils.colors import get_nick_colour, get_nick_colour_qcolor
from src.gui.utils.formatters import irc_to_html
from src.gui.dialogs.network_list import NetworkListDialogue
from src.gui.dialogs.settings import SettingsDialogue
from src.gui.components.chat_input import ChatInput
from src.gui.mixins.event_handlers import EventHandlerMixin
from src.plugins.loader import PluginLoader

DEFAULT_WINDOW_X = 100
DEFAULT_WINDOW_Y = 100
DEFAULT_WINDOW_WIDTH = 1100
DEFAULT_WINDOW_HEIGHT = 700

MESSAGE_BATCH_INTERVAL_MS = 100
NETWORK_LIST_DELAY_MS = 100
MAX_MESSAGES_PER_BATCH = 500

NICK_PREFIXES = ('~', '&', '@', '%', '+')
NICK_RANK_MAP = {'~': 0, '&': 1, '@': 2, '%': 3, '+': 4}

class MainWindow(QMainWindow, EventHandlerMixin):
    def __init__(self):
        super().__init__()
        self.current_nw = None
        self.current_target = ""
        self.tree_items = {}
        self.clients = {}
        self.buffers = {}
        self.recent_activity = {}  # Track recent join/part activity for smart filtering
        
        self.load_settings()
        
        self.setObjectName("PyeChat")
        self.setWindowTitle("PyeChat")
        
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets'))
        # Prefer vector icon if available, fall back to PNG/ICO
        for name in ('pyechat.svg', 'pyechat.png', 'pyechat_fixed.png', 'pyechat.ico'):
            icon_path = os.path.join(assets_dir, name)
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break
        
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

        # Message queue and batching timer (must be initialized early)
        self.msg_queue = []
        self.msg_timer = QTimer()
        self.msg_timer.setInterval(MESSAGE_BATCH_INTERVAL_MS)
        self.msg_timer.timeout.connect(self.flush_messages)
        self.msg_timer.start()

        # Re-apply theme after window is fully initialized
        QTimer.singleShot(100, self.apply_theme)

        # Load scripts/plugins
        self.plugin_loader = PluginLoader(self)
        QTimer.singleShot(500, self.plugin_loader.load_all)

        # Backwards-compatible scheduling of network list. Also ensure it opens when
        # the main window is first shown in case earlier scheduling was missed.
        if not self.settings.get("skip_network_list", False):
            QTimer.singleShot(NETWORK_LIST_DELAY_MS, self.openNetworkListDialogue)
            self._open_network_list_on_show = True

        # Input history (for up/down navigation)
        self.input_history = []
        self.history_index = 0
        self.history_draft = ""

    def history_prev(self):
        """Return previous history entry, or None."""
        if not self.input_history: return None
        # if at end, store draft
        if self.history_index == len(self.input_history):
            try:
                self.history_draft = self.input.toPlainText()
            except Exception:
                self.history_draft = ""
        if self.history_index > 0:
            self.history_index -= 1
            return self.input_history[self.history_index]
        return None

    def history_next(self):
        """Return next history entry, or draft, or None."""
        if not self.input_history: return None
        if self.history_index < len(self.input_history) - 1:
            self.history_index += 1
            return self.input_history[self.history_index]
        elif self.history_index == len(self.input_history) - 1:
            self.history_index = len(self.input_history)
            return self.history_draft
        return None


    def load_settings(self):
        settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'settings.json'))
        try:
            with open(settings_path, 'r') as f: self.settings = json.load(f)
            for k, v in self.settings.items():
                if v == "#3584E4" or v == "#3584e4": self.settings[k] = "#E95420"
        except (FileNotFoundError, json.JSONDecodeError):
            from src.gui.dialogs.settings import SettingsDialogue
            temp = SettingsDialogue(None, {})
            self.settings = temp.get_default_events_v2()

    def save_settings(self):
        settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'settings.json'))
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w') as f: json.dump(self.settings, f, indent=4)

    def apply_theme(self):
        s = self.settings
        if s.get("use_system_theme", True):
            app = QApplication.instance()
            if app:
                palette = app.style().standardPalette()
                palette.setColor(QPalette.Highlight, QColor("#E95420"))
                palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
                app.setPalette(palette)
            self.setStyleSheet("QTreeWidget { border: none; outline: none; } QTreeWidget::item { padding: 2px; }")
            return
        
        bg, fg = s.get("bg_colour", "#1e1e1e"), s.get("fg_colour", "#ffffff")
        tree_bg, tree_fg = s.get("tree_bg", "#252526"), s.get("tree_fg", "#cccccc")
        nick_bg, nick_fg = s.get("nick_bg", "#252526"), s.get("nick_fg", "#cccccc")
        
        # Clear any application palette so stylesheet can take effect
        app = QApplication.instance()
        if app:
            app.setPalette(app.style().standardPalette())
        
        # DON'T SET ANY STYLESHEET - it overrides palettes!
        # Just use palettes directly on widgets
        
        # Apply directly to widgets to force override
        if hasattr(self, 'tree'):
            palette = self.tree.palette()
            palette.setColor(QPalette.Base, QColor(tree_bg))
            palette.setColor(QPalette.Text, QColor(tree_fg))
            palette.setColor(QPalette.WindowText, QColor(tree_fg))
            palette.setColor(QPalette.Highlight, QColor(s.get('tree_sel_bg', '#E95420')))
            palette.setColor(QPalette.HighlightedText, QColor(s.get('tree_sel_fg', '#ffffff')))
            self.tree.setPalette(palette)
            self.tree.setAutoFillBackground(True)
            # Also set stylesheet directly on widget as backup
            self.tree.setStyleSheet(f"QTreeWidget {{ background-color: {tree_bg}; color: {tree_fg}; border: none; }} QTreeWidget::item {{ color: {tree_fg}; }} QTreeWidget::item:selected {{ background-color: {s.get('tree_sel_bg', '#E95420')}; color: {s.get('tree_sel_fg', '#ffffff')}; }}")
            
        if hasattr(self, 'nicks'):
            palette = self.nicks.palette()
            palette.setColor(QPalette.Base, QColor(nick_bg))
            palette.setColor(QPalette.Text, QColor(nick_fg))
            palette.setColor(QPalette.WindowText, QColor(nick_fg))
            palette.setColor(QPalette.Highlight, QColor(s.get('nick_sel_bg', '#E95420')))
            palette.setColor(QPalette.HighlightedText, QColor(s.get('nick_sel_fg', '#ffffff')))
            self.nicks.setPalette(palette)
            self.nicks.setAutoFillBackground(True)
            # Don't set item color in stylesheet if nick coloring is enabled, so individual colors can show
            if s.get("nick_colouring", True):
                self.nicks.setStyleSheet(f"QListWidget {{ background-color: {nick_bg}; border: none; }} QListWidget::item:selected {{ background-color: {s.get('nick_sel_bg', '#E95420')}; color: {s.get('nick_sel_fg', '#ffffff')}; }}")
            else:
                self.nicks.setStyleSheet(f"QListWidget {{ background-color: {nick_bg}; color: {nick_fg}; border: none; }} QListWidget::item {{ color: {nick_fg}; }} QListWidget::item:selected {{ background-color: {s.get('nick_sel_bg', '#E95420')}; color: {s.get('nick_sel_fg', '#ffffff')}; }}")
        
        # Still apply stylesheet to OTHER widgets (chat, input, etc)
        style = f"""
            QMainWindow, QDialog {{ background-color: {bg}; color: {fg}; }}
            QTextBrowser {{ 
                background-color: {bg}; 
                color: {fg}; 
                border: none; 
                padding: 4px;
            }}
            QPlainTextEdit {{ 
                background-color: {s.get('input_bg', '#3c3c3c')}; 
                color: {s.get('input_fg', '#ffffff')}; 
                border: 1px solid {s.get('input_border', '#cccccc')}; 
                border-radius: 2px;
                padding: 4px;
            }}
            QLabel#topic {{ 
                background-color: {s.get('topic_bg', '#333333')}; 
                color: {s.get('topic_fg', '#ffffff')}; 
                padding: 6px; 
                border-bottom: 1px solid {s.get('border_colour', '#3e3e42')};
            }}
            QSplitter::handle {{ 
                background-color: {s.get('border_colour', '#3e3e42')}; 
                width: 1px;
            }}
            QTreeWidget::item {{
                padding: 3px 2px;
            }}
            QListWidget::item {{
                padding: 2px 4px;
            }}
        """
        self.setStyleSheet(style)

        # Apply font if configured
        font_str = s.get('font')
        if font_str:
            try:
                f = QFont()
                f.fromString(font_str)
                # Apply to major widgets
                if hasattr(self, 'chat'):
                    self.chat.setFont(f)
                if hasattr(self, 'input'):
                    self.input.setFont(f)
                if hasattr(self, 'nicks'):
                    self.nicks.setFont(f)
                if hasattr(self, 'tree'):
                    self.tree.setFont(f)
                if hasattr(self, 'topic'):
                    self.topic.setFont(f)
                # Also re-render existing chat contents to ensure font is used
                # by re-setting the HTML/text which forces a reflow using new font
                for buf_key, buf in self.buffers.items():
                    if buf['messages'] and self.current_nw == buf_key[0] and self.current_target == buf_key[1]:
                        # current buffer: re-apply HTML
                        self.chat.setUpdatesEnabled(False)
                        self.chat.setHtml("".join(buf['messages']))
                        self.chat.moveCursor(QTextCursor.End)
                        self.chat.setUpdatesEnabled(True)
            except Exception:
                pass

    def setup_ui(self):
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFixedWidth(200)
        self.tree.itemClicked.connect(self.on_tree_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_tree_context_menu)
        self.tree.setAutoFillBackground(True)
        self.splitter.addWidget(self.tree)

        self.mid_container = QWidget()
        self.mid_layout = QVBoxLayout(self.mid_container)
        self.mid_layout.setContentsMargins(0, 0, 0, 0)
        self.mid_layout.setSpacing(0)
        
        self.topic = QLabel("")
        self.topic.setObjectName("topic")
        self.topic.setMinimumWidth(0)
        self.topic.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        
        self.chat = QTextBrowser()
        self.chat.setReadOnly(True)
        self.chat.setOpenExternalLinks(True)
        self.chat.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chat.customContextMenuRequested.connect(self.on_chat_context_menu)
        
        self.input = ChatInput(self)
        
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
        self.nicks.setAutoFillBackground(True)
        self.splitter.addWidget(self.nicks)

        self.layout.addWidget(self.splitter)

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
        
        client = IRCClient(name, nw['host'], nw['port'], nw['nick'], nw['realname'], 
                          nw.get('channels', []), nw.get('use_ssl', False), nw.get('password'), 
                          self.settings.get("auto_reconnect", True),
                          nw.get('sasl_method'), nw.get('sasl_user'), nw.get('sasl_pass'),
                          nw.get('auto_commands', []))
        self.clients[name] = client
        client.received_message.connect(lambda t, m, tags, n=name: self.on_message(n, t, m, tags))
        client.received_nick_list.connect(lambda d, n=name: self.on_nick(n, d))
        client.received_topic.connect(lambda c, t, n=name: self.on_topic(n, c, t))
        client.received_topic_meta.connect(lambda c, s, ts, n=name: self.on_topic_meta(n, c, s, ts))
        client.parted_channel.connect(lambda c, ni, n=name: self.on_part(n, c, ni))
        client.nick_changed.connect(lambda o, ni, n=name: self.on_nick_change(n, o, ni))
        client.received_kick.connect(lambda c, t, k, r, n=name: self.on_kick(n, c, t, k, r))
        client.received_mode.connect(lambda c, s, m, n=name: self.on_mode(n, c, s, m))
        client.received_invite.connect(lambda c, s, ni, n=name: self.on_invite(n, c, s, ni))
        client.received_notice.connect(lambda t, s, m, n=name: self.on_notice(n, t, s, m))
        client.received_action.connect(lambda t, s, m, n=name: self.on_action(n, t, s, m))
        client.received_whois.connect(lambda d, t, n=name: self.on_whois(n, d, t))
        client.received_quit.connect(lambda ni, r, n=name: self.on_quit(n, ni, r))
        client.event_received.connect(lambda c, s, a, t, n=name: self.on_event_received(n, c, s, a, t))
        client.disconnected_from_server.connect(lambda n=name: self.on_disconnect(n))
        self.switch_buffer(name, "")
        client.connect_to_host()

    def setup_buffer(self, nw, target):
        if (nw, target) not in self.buffers: 
            self.buffers[(nw, target)] = {"messages": [], "nicks": [], "topic": "", "activity": False, "highlight": False}

    def switch_buffer(self, nw, target):
        if self.current_nw == nw and self.current_target == target: return
        self.current_nw, self.current_target = nw, target
        self.setup_buffer(nw, target)
        buf = self.buffers[(nw, target)]
        buf["activity"] = buf["highlight"] = False
        
        it = self.find_item(nw, target)
        if it:
            it.setForeground(0, QPalette().color(QPalette.WindowText))
            font = it.font(0)
            font.setBold(not target)
            it.setFont(0, font)

        self.chat.setUpdatesEnabled(False)
        self.chat.clear()
        if buf["messages"]:
            self.chat.setHtml("".join(buf["messages"]))
            self.chat.moveCursor(QTextCursor.End)
        self.chat.setUpdatesEnabled(True)
        
        topic_text = buf["topic"] or target
        if buf["nicks"]: topic_text = f"({len(buf['nicks'])}) {topic_text}"
        self.topic.setText(topic_text)
        self.topic.setToolTip(buf["topic"] or target)
        self.render_nick_list()
        
        msg = f"NW: {nw}"
        if nw in self.clients: msg += f" | Nick: {self.clients[nw].nickname}"
        if target: msg += f" | Buf: {target}"
        self.statusBar().showMessage(msg)

    def on_tree_click(self, item, col):
        p = item.parent()
        self.switch_buffer(p.text(0) if p else item.text(0), item.text(0) if p else "")
        self.input.setFocus()

    def on_message(self, nw, target, msg, tags=None):
        if tags is None: tags = {}
        if not target and self.current_nw == nw: target = self.current_target

        # If the target looks like a hostname (server) and this is not a private message, treat it as network status
        if target and not target.startswith(('#', '&')) and not tags.get('is_private') and '.' in target:
            target = ""

        self.setup_buffer(nw, target)
        
        # Suppress numeric server replies (like [366] End of NAMES) in channel windows
        if target and target.startswith(('#', '&')) and msg.startswith('[') and len(msg) >= 5 and msg[1:4].isdigit() and msg[4] == ']' and not self.settings.get('show_numeric_replies', False):
            return
        
        formatted_msg = msg
        is_highlight = False
        sender = None
        if msg.startswith('<') and '>' in msg:
            sender = msg[1:msg.find('>')]
            content = msg[msg.find('>')+1:]

            # Track user activity for smart filtering
            if sender and target:
                self._track_user_activity(nw, target, sender)

            # If this is a channel message, try to display any status prefix
            # (e.g., @, +, &, ~) that appears in the nick list so users' status
            # is visible inline next to their nick in messages.
            display_sender = sender
            try:
                if target and target.startswith(('#', '&')):
                    buf = self.buffers.get((nw, target), {})
                    prefix_chars = ''.join(NICK_PREFIXES) + ' '
                    nicks_in_channel = buf.get('nicks', [])
                    for n in nicks_in_channel:
                        raw = n.lstrip(prefix_chars)
                        if raw.lower() == sender.lower():
                            # preserve any leading prefix characters
                            prefix = n[:len(n) - len(raw)]
                            if prefix:
                                # Some servers may annotate multiple status prefixes (e.g., '&@').
                                # Choose the single highest-priority prefix to display
                                best = None
                                best_rank = 999
                                for ch in prefix:
                                    r = NICK_RANK_MAP.get(ch)
                                    if r is not None and r < best_rank:
                                        best = ch; best_rank = r
                                if best:
                                    display_sender = f"{best}{sender}"
                                else:
                                    display_sender = f"{prefix}{sender}"
                            break
            except Exception:
                pass

            if self.settings.get("nick_colouring", True):
                colour = get_nick_colour(sender, self.settings.get("bg_colour", "#ffffff"))
                formatted_msg = f'<span style="color: {colour}; font-weight: bold;">&lt;{display_sender}&gt;</span> {irc_to_html(content)}'
            else:
                formatted_msg = f'&lt;{display_sender}&gt; {irc_to_html(content)}'
            if self.settings.get("highlight_mentions", True) and self.clients[nw].nickname.lower() in msg.lower():
                is_highlight = True
        else:
            formatted_msg = irc_to_html(msg)

        ts = ""
        if self.settings.get("show_timestamps", True):
            fmt, colour = self.settings.get("ts_format", "[%H:%M:%S]"), self.settings.get("ts_colour", "#888")
            t_tag = tags.get('time')
            dt = datetime.datetime.fromisoformat(t_tag.replace('Z', '+00:00')) if t_tag else datetime.datetime.now()
            ts = f'<span style="color: {colour};">{dt.strftime(fmt)} </span>'

        if is_highlight:
            bg, border = self.settings.get("hl_bg", "rgba(255, 204, 0, 0.1)"), self.settings.get("hl_border", "#ffcc00")
            final_line = f'<div style="background-color: {bg}; border-left: 3px solid {border}; padding-left: 5px;">{ts}{formatted_msg}</div>'
        else:
            style = f' style="color: {tags["fmt_color"]};"' if tags.get("fmt_color") else ""
            final_line = f'<div{style}>{ts}{formatted_msg}</div>'

        buf = self.buffers[(nw, target)]
        buf["messages"].append(final_line)
        if len(buf["messages"]) > 2500: buf["messages"].pop(0)
        if target and not self.find_item(nw, target): self.add_tree_item(nw, target)
        self.msg_queue.append((nw, target, final_line))
        
        if nw == self.current_nw and target == self.current_target: return
        it = self.find_item(nw, target)
        if it:
            if is_highlight:
                buf["highlight"] = True
                it.setForeground(0, QColor("#E95420"))
            elif not buf["highlight"]:
                buf["activity"] = True
                it.setForeground(0, QColor("#ffffff" if self.settings.get("bg_colour", "#1e1e1e") != "#ffffff" else "#000000"))
            f = it.font(0); f.setBold(True); it.setFont(0, f)

    def flush_messages(self):
        if not self.msg_queue: return
        batch = self.msg_queue[:MAX_MESSAGES_PER_BATCH]
        self.msg_queue = self.msg_queue[MAX_MESSAGES_PER_BATCH:]
        updates = {}
        for nw, target, line in batch:
            if (nw, target) not in updates: updates[(nw, target)] = []
            updates[(nw, target)].append(line)
        if (self.current_nw, self.current_target) in updates:
            bar = self.chat.verticalScrollBar()
            at_bottom = bar.value() >= bar.maximum() - 20
            self.chat.append("".join(updates[(self.current_nw, self.current_target)]))
            if at_bottom: self.chat.moveCursor(QTextCursor.End)

    def flush_nicks(self):
        if (self.current_nw, self.current_target) in self.nick_update_queued: self.render_nick_list()
        self.nick_update_queued.clear()

    def render_nick_list(self):
        self.nicks.setUpdatesEnabled(False); self.nicks.clear()
        if not self.current_nw or not self.current_target: self.nicks.setUpdatesEnabled(True); return
        buf = self.buffers.get((self.current_nw, self.current_target))
        if not buf: self.nicks.setUpdatesEnabled(True); return
        
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        sorted_nicks = sorted(buf["nicks"], key=lambda x: (NICK_RANK_MAP.get(x[0], 5), x.lstrip(prefix_chars).lower()))
        
        # Apply colors to each nick if nick coloring is enabled
        if self.settings.get("nick_colouring", True):
            for nick_with_prefix in sorted_nicks:
                # Strip prefix to get actual nickname for color calculation
                clean_nick = nick_with_prefix.lstrip(prefix_chars)
                nick_color = get_nick_colour_qcolor(clean_nick, self.settings.get("nick_bg", "#1e1e1e"))
                
                item = QListWidgetItem(nick_with_prefix)
                item.setForeground(nick_color)
                self.nicks.addItem(item)
        else:
            self.nicks.addItems(sorted_nicks)
            
        self.nicks.setUpdatesEnabled(True)

    def find_item(self, nw, target): return self.tree_items.get((nw, target))
    def add_tree_item(self, nw, target):
        if not target or (nw, target) in self.tree_items: return
        p = self.find_item(nw, "")
        if p:
            it = QTreeWidgetItem(p); it.setText(0, target); self.tree_items[(nw, target)] = it

    def remove_tree_item(self, nw, target):
        it = self.tree_items.pop((nw, target), None)
        if it and it.parent(): it.parent().removeChild(it)

    def handle_exec_command(self, args):
        """Handle /exec command - execute shell commands and display output."""
        if not args:
            self.on_message(self.current_nw, self.current_target or "", "Usage: /exec [-o] <command>")
            return
        
        # Parse flags
        send_to_channel = False
        command = args
        
        if args.startswith('-o '):
            send_to_channel = True
            command = args[3:]
        elif args.startswith('-o'):
            send_to_channel = True
            command = args[2:].lstrip()
        
        if not command:
            self.on_message(self.current_nw, self.current_target or "", "Usage: /exec [-o] <command>")
            return
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout.strip()
            if result.stderr:
                output += "\n" + result.stderr.strip()
            
            if not output:
                output = f"Command completed (exit code: {result.returncode})"
            
            # Split output into lines
            lines = output.split('\n')
            
            if send_to_channel and self.current_target and self.current_nw in self.clients:
                # Send each line to channel
                c = self.clients[self.current_nw]
                for line in lines:
                    if line:
                        c.send_command(f"PRIVMSG {self.current_target} :{line}")
                        self.on_message(self.current_nw, self.current_target, f"<{c.nickname}> {line}")
            else:
                # Display locally
                target = self.current_target or ""
                for line in lines:
                    if line:
                        self.on_message(self.current_nw, target, f"[exec] {line}")
        
        except subprocess.TimeoutExpired:
            self.on_message(self.current_nw, self.current_target or "", "[exec] Error: Command timed out (10s limit)")
        except Exception as e:
            self.on_message(self.current_nw, self.current_target or "", f"[exec] Error: {str(e)}")

    def on_send(self):
        txt = self.input.toPlainText().strip()
        if not txt or not self.current_nw or self.current_nw not in self.clients: return
        c = self.clients[self.current_nw]

        # Store in history (non-empty commands and messages)
        def _add_history(line):
            if not line: return
            if not self.input_history or self.input_history[-1] != line:
                self.input_history.append(line)
            self.history_index = len(self.input_history)
            self.history_draft = ""

        if txt.startswith('/'):
            parts = txt[1:].split(' ', 1)
            raw_cmd, args = parts[0], parts[1] if len(parts) > 1 else ""
            cmd = raw_cmd.upper()

            # Short command aliases
            COMMAND_ALIASES = {
                'J': 'JOIN', 'JOIN': 'JOIN',
                'NS': 'NICKSERV', # kept for compatibility, handled below
            }

            # Common services aliases -> map to service nick
            SERVICE_ALIASES = {
                'NS': 'NickServ', 'OS': 'OperServ', 'BS': 'BotServ', 'CS': 'ChanServ',
                'MS': 'MemoServ', 'HS': 'HostServ'
            }

            # Expand simple aliases
            if cmd in COMMAND_ALIASES:
                cmd = COMMAND_ALIASES[cmd]

            # If service alias, send PRIVMSG to that service
            if cmd in SERVICE_ALIASES:
                service = SERVICE_ALIASES[cmd]
                if args:
                    c.send_command(f"PRIVMSG {service} :{args}")
                    self.on_message(self.current_nw, service, f"<{c.nickname}> {args}")
                    _add_history(txt)
                else:
                    self.switch_buffer(self.current_nw, service)
                self.input.clear()
                return

            if cmd == "JOIN": c.send_command(f"JOIN {args}")
            elif cmd == "EXEC": self.handle_exec_command(args)
            elif cmd in ["MSG", "QUERY"]:
                m_parts = args.split(' ', 1)
                if len(m_parts) == 2:
                    c.send_command(f"PRIVMSG {m_parts[0]} :{m_parts[1]}")
                    self.on_message(self.current_nw, m_parts[0], f"<{c.nickname}> {m_parts[1]}")
            elif cmd == "ME":
                if self.current_target:
                    c.send_command(f"PRIVMSG {self.current_target} :\x01ACTION {args}\x01")
                    self.on_message(self.current_nw, self.current_target, f"* {c.nickname} {args}")
                    _add_history(txt)
            elif cmd == "SYSINFO":
                # Built-in system info command - send formatted info to the current target (channel or user)
                try:
                    from src.gui.utils.sysinfo import get_sysinfo
                    info = get_sysinfo()
                    target = self.current_target
                    if not target:
                        # No buffer selected
                        self.on_message(self.current_nw, "", "*** Error: No target buffer to send SYSINFO to")
                    else:
                        # Send to server so others can see it
                        c.send_command(f"PRIVMSG {target} :{info}")
                        # Also display locally
                        self.on_message(self.current_nw, target, f"<{c.nickname}> {info}")
                        _add_history(txt)
                except Exception as e:
                    self.on_message(self.current_nw, self.current_target or "", f"*** Error: {e}")
            else:
                # Fallback: send raw command to server
                c.send_command(txt[1:])
                _add_history(txt)
            self.input.clear()
            return
        elif self.current_target:
            c.send_command(f"PRIVMSG {self.current_target} :{txt}")
            self.on_message(self.current_nw, self.current_target, f"<{c.nickname}> {txt}")
            # Add to history for editing
            if txt:
                if not self.input_history or self.input_history[-1] != txt:
                    self.input_history.append(txt)
                self.history_index = len(self.input_history)
                self.history_draft = ""
        self.input.clear()

    def on_nick(self, nw, data):
        chan, nick = data
        self.on_nick_inner(nw, chan, nick)

    def on_nick_inner(self, nw, chan, nick):
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        raw_nick = nick.lstrip(prefix_chars)
        self.setup_buffer(nw, chan)
        if not self.find_item(nw, chan): self.add_tree_item(nw, chan)
        nicks = self.buffers[(nw, chan)]["nicks"]
        for i, n in enumerate(nicks):
            if n.lstrip(prefix_chars).lower() == raw_nick.lower():
                nicks[i] = nick; break
        else: nicks.append(nick)
        if self.current_nw == nw and self.current_target == chan:
            self.nick_update_queued.add((nw, chan))
            if not self.nick_timer.isActive(): self.nick_timer.start(100)

    def show_sysinfo(self, target=None):
        """Gather and display SYSINFO in the specified buffer (or current).
        This also sends the info as a PRIVMSG so other users can see it."""
        nw = self.current_nw
        if not nw or nw not in self.clients:
            return
        target = target or self.current_target or ""
        if not target:
            self.on_message(nw, "", "*** Error: No target to send SYSINFO to")
            return
        try:
            from src.gui.utils.sysinfo import get_sysinfo
            info = get_sysinfo()
            nick = self.clients[nw].nickname
            # Send to server so others can see it
            self.clients[nw].send_command(f"PRIVMSG {target} :{info}")
            # Also display locally
            self.on_message(nw, target, f"<{nick}> {info}")
        except Exception as e:
            self.on_message(nw, target, f"*** Error gathering system info: {e}")

    # ------------------ Operator command helpers ------------------
    def _add_oper_menu(self, menu, nick=None):
        """Add an Operator Commands submenu to `menu`. If `nick` is supplied
        some commands will be pre-filled for convenience."""
        oper_menu = menu.addMenu("Operator Commands")
        oper_menu.addAction("Become OPER...").triggered.connect(lambda: self._oper_become())
        oper_menu.addAction("Kill user...").triggered.connect(lambda: self._oper_kill(nick) if nick else self._oper_kill())
        oper_menu.addAction("K-Line (ban)...").triggered.connect(lambda: self._oper_ban('KLINE', f"{nick}!*@*" if nick else ""))
        oper_menu.addAction("G-Line (global ban)...").triggered.connect(lambda: self._oper_ban('GLINE', f"{nick}!*@*" if nick else ""))
        oper_menu.addAction("Z-Line (IP ban)...").triggered.connect(lambda: self._oper_ban('ZLINE', ""))
        oper_menu.addAction("Unban (UNKLINE/UNGLINE)...").triggered.connect(lambda: self._oper_unban())
        oper_menu.addAction("WALLOPS...").triggered.connect(lambda: self._oper_wallops())
        oper_menu.addAction("SQUIT server...").triggered.connect(lambda: self._oper_squit())
        oper_menu.addSeparator()
        oper_menu.addAction("RESTART server").triggered.connect(lambda: self._oper_confirm('RESTART'))
        oper_menu.addAction("DIE server").triggered.connect(lambda: self._oper_confirm('DIE'))
        oper_menu.addSeparator()
        oper_menu.addAction("Send raw operator command...").triggered.connect(lambda: self._oper_raw())

    def _oper_become(self):
        from PyQt5.QtWidgets import QInputDialog
        user, ok = QInputDialog.getText(self, "Become OPER", "Operator username:")
        if not ok or not user: return
        pwd, ok2 = QInputDialog.getText(self, "Become OPER", "Operator password:", QInputDialog.Normal)
        if not ok2: return
        cmd = f"OPER {user} {pwd}"
        self._oper_confirm_and_send(cmd)

    def _oper_kill(self, nick=None):
        from PyQt5.QtWidgets import QInputDialog
        if not nick:
            nick, ok = QInputDialog.getText(self, "Kill User", "Nick to KILL:")
            if not ok or not nick: return
        reason, ok = QInputDialog.getText(self, "Kill User", f"Reason for killing {nick}:")
        if not ok: return
        cmd = f"KILL {nick} :{reason}" if reason else f"KILL {nick}"
        self._oper_confirm_and_send(cmd, warn=True)

    def _oper_ban(self, kind, default_mask=""):
        from PyQt5.QtWidgets import QInputDialog
        mask, ok = QInputDialog.getText(self, f"{kind}", "Ban mask:", text=default_mask)
        if not ok or not mask: return
        reason, ok2 = QInputDialog.getText(self, f"{kind}", "Reason:")
        if not ok2: return
        cmd = f"{kind} {mask} :{reason}" if reason else f"{kind} {mask}"
        self._oper_confirm_and_send(cmd, warn=True)

    def _oper_unban(self):
        from PyQt5.QtWidgets import QInputDialog
        mask, ok = QInputDialog.getText(self, "Unban", "Ban mask to remove (exact):")
        if not ok or not mask: return
        # Try both UNGLINE and UNKLINE as servers differ
        from PyQt5.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Confirm", "Send UNGLINE (Yes) or UNKLINE (No)?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            cmd = f"UNGLINE {mask}"
        else:
            cmd = f"UNKLINE {mask}"
        self._oper_confirm_and_send(cmd)

    def _oper_wallops(self):
        from PyQt5.QtWidgets import QInputDialog
        msg, ok = QInputDialog.getText(self, "WALLOPS", "Message to WALLOPS:")
        if not ok or not msg: return
        cmd = f"WALLOPS :{msg}"
        self._oper_confirm_and_send(cmd)

    def _oper_squit(self):
        from PyQt5.QtWidgets import QInputDialog
        srv, ok = QInputDialog.getText(self, "SQUIT", "Server to SQUIT:")
        if not ok or not srv: return
        reason, ok2 = QInputDialog.getText(self, "SQUIT", "Reason:")
        if not ok2: return
        cmd = f"SQUIT {srv} :{reason}" if reason else f"SQUIT {srv}"
        self._oper_confirm_and_send(cmd, warn=True)

    def _oper_confirm(self, cmd):
        from PyQt5.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Confirm", f"Really send '{cmd}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._oper_confirm_and_send(cmd, warn=True)

    def _oper_raw(self):
        from PyQt5.QtWidgets import QInputDialog
        cmd, ok = QInputDialog.getText(self, "Raw Operator Command", "IRC command:")
        if not ok or not cmd: return
        self._oper_confirm_and_send(cmd, warn=True)

    def _oper_confirm_and_send(self, cmd, warn=False):
        from PyQt5.QtWidgets import QMessageBox
        if warn:
            if QMessageBox.warning(self, "Dangerous Command", f"This command may be disruptive:\n{cmd}\n\nAre you sure?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
        nw = self.current_nw
        if not nw or nw not in self.clients:
            self.on_message("", "", "*** Error: Not connected to any network")
            return
        try:
            self.clients[nw].send_command(cmd)
            self.on_message(nw, self.current_target or "", f"*** Sent oper command: {cmd}")
        except Exception as e:
            self.on_message(nw, self.current_target or "", f"*** Error sending oper command: {e}")

    def on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        menu = QMenu()
        p = item.parent()
        if not p:
            nw = item.text(0)
            if nw in self.clients: menu.addAction("Disconnect").triggered.connect(lambda: self.clients[nw].socket.disconnectFromHost())
        else:
            nw, target = p.text(0), item.text(0)
            if target.startswith(('#', '&')): menu.addAction("Part").triggered.connect(lambda: self.clients[nw].send_command(f"PART {target}"))
            menu.addAction("Close").triggered.connect(lambda: (self.remove_tree_item(nw, target), self.switch_buffer(nw, "") if self.current_target == target else None))
            # Provide quick sysinfo on channel (tree context)
            if target.startswith(('#', '&')):
                menu.addAction("Sysinfo").triggered.connect(lambda: self.show_sysinfo(target))
                # Channel-level operator commands
                try:
                    self._add_oper_menu(menu, None)
                except Exception:
                    pass
        menu.exec_(self.tree.mapToGlobal(pos))

    def on_nick_context_menu(self, pos):
        item = self.nicks.itemAt(pos)
        if not item or not self.current_nw or not self.current_target: return
        
        menu = QMenu()
        nick_with_prefix = item.text()
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        nick = nick_with_prefix.lstrip(prefix_chars)
        
        # Information actions
        menu.addAction("Whois").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"WHOIS {nick} {nick}"))
        menu.addAction("Direct Message").triggered.connect(lambda: self.switch_buffer(self.current_nw, nick))
        menu.addAction("Sysinfo").triggered.connect(lambda: self.show_sysinfo(self.current_target))
        menu.addSeparator()
        
        # Channel operations (only if in a channel)
        if self.current_target.startswith(('#', '&')):
            # Op/Deop submenu
            op_menu = menu.addMenu("Give Operator")
            op_menu.addAction("Owner (+q)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +q {nick}"))
            op_menu.addAction("Admin (+a)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +a {nick}"))
            op_menu.addAction("Op (+o)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +o {nick}"))
            op_menu.addAction("Half-Op (+h)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +h {nick}"))
            op_menu.addAction("Voice (+v)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +v {nick}"))
            
            deop_menu = menu.addMenu("Revoke Operator")
            deop_menu.addAction("Owner (-q)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -q {nick}"))
            deop_menu.addAction("Admin (-a)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -a {nick}"))
            deop_menu.addAction("Op (-o)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -o {nick}"))
            deop_menu.addAction("Half-Op (-h)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -h {nick}"))
            deop_menu.addAction("Voice (-v)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -v {nick}"))
            
            menu.addSeparator()
            
            # Kick/Ban actions
            menu.addAction("Kick").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"KICK {self.current_target} {nick}"))
            menu.addAction("Kick with Reason...").triggered.connect(lambda: self.kick_with_reason(nick))
            menu.addAction("Ban").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +b {nick}!*@*"))
            menu.addAction("Kick + Ban").triggered.connect(lambda: (
                self.clients[self.current_nw].send_command(f"MODE {self.current_target} +b {nick}!*@*"),
                self.clients[self.current_nw].send_command(f"KICK {self.current_target} {nick}")
            ))
            menu.addSeparator()
        
        # User actions
        menu.addAction("Ignore User").triggered.connect(lambda: self.on_message(self.current_nw, self.current_target, f"*** Ignoring {nick} (not yet implemented)"))
        menu.addAction("Copy Nickname").triggered.connect(lambda: QApplication.clipboard().setText(nick))
            
        # Advanced operator commands
        try:
            self._add_oper_menu(menu, nick)
        except Exception:
            pass
        
        menu.exec_(self.nicks.mapToGlobal(pos))
    
    def on_chat_context_menu(self, pos):
        """Context menu for chat area - can right-click on nicknames in messages."""
        cursor = self.chat.cursorForPosition(pos)
        cursor.select(cursor.WordUnderCursor)
        word = cursor.selectedText().strip('<>:,')
        
        # Check if word looks like a nickname (not a URL, not empty, reasonable length)
        if not word or len(word) > 30 or '/' in word or '.' in word and len(word.split('.')) > 2:
            # Show default text browser context menu
            return
        
        # Try to find this word in the current channel's nicklist
        if self.current_nw and self.current_target:
            buf = self.buffers.get((self.current_nw, self.current_target))
            if buf:
                prefix_chars = ''.join(NICK_PREFIXES) + ' '
                nicks_in_channel = [n.lstrip(prefix_chars).lower() for n in buf.get("nicks", [])]
                
                if word.lower() in nicks_in_channel:
                    # Found a valid nickname token — perform some additional checks to avoid
                    # accidental matches inside URLs or other text. Prefer explicit
                    # nickname markers (e.g. surrounding < and >) or bold formatting used
                    # when rendering nicknames.
                    start, end = cursor.selectionStart(), cursor.selectionEnd()
                    doc_text = self.chat.toPlainText()
                    char_before = doc_text[start-1] if start > 0 else ''
                    char_after = doc_text[end] if end < len(doc_text) else ''

                    # If nickname is wrapped like <nick> in the chat, accept it.
                    if char_before == '<' and char_after == '>':
                        self.show_nick_menu_for_name(word, pos)
                        return

                    # Otherwise, check the text formatting at the cursor position
                    fmt = cursor.charFormat()
                    try:
                        if fmt.fontWeight() >= QFont.Bold:
                            self.show_nick_menu_for_name(word, pos)
                            return
                    except Exception:
                        pass
                    # No strong indication this was a nickname click; fall through to
                    # the default context menu instead of showing the nick menu.
        
        # Not a nickname: show default menu with copy option, and channel management if in a channel
        menu = QMenu()
        if cursor.hasSelection():
            menu.addAction("Copy").triggered.connect(lambda: QApplication.clipboard().setText(cursor.selectedText()))
        # Channel actions
        from src.gui.dialogs.channel_management import ChannelManagementDialogue
        if self.current_target and self.current_target.startswith(('#', '&')):
            menu.addSeparator()
            menu.addAction("Channel Management").triggered.connect(lambda: ChannelManagementDialogue(self, self.current_nw, self.current_target, self.clients[self.current_nw]).exec_())
            menu.addAction("Sysinfo").triggered.connect(lambda: self.show_sysinfo(self.current_target))
        menu.exec_(self.chat.mapToGlobal(pos))
    
    def show_nick_menu_for_name(self, nick, pos):
        """Show the same context menu as nicklist for a clicked nickname."""
        menu = QMenu()
        
        # Information actions
        menu.addAction("Whois").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"WHOIS {nick} {nick}"))
        menu.addAction("Direct Message").triggered.connect(lambda: self.switch_buffer(self.current_nw, nick))
        menu.addSeparator()
        
        # Channel operations (only if in a channel)
        if self.current_target.startswith(('#', '&')):
            # Op/Deop submenu
            op_menu = menu.addMenu("Give Operator")
            op_menu.addAction("Owner (+q)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +q {nick}"))
            op_menu.addAction("Admin (+a)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +a {nick}"))
            op_menu.addAction("Op (+o)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +o {nick}"))
            op_menu.addAction("Half-Op (+h)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +h {nick}"))
            op_menu.addAction("Voice (+v)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +v {nick}"))
            
            deop_menu = menu.addMenu("Revoke Operator")
            deop_menu.addAction("Owner (-q)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -q {nick}"))
            deop_menu.addAction("Admin (-a)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -a {nick}"))
            deop_menu.addAction("Op (-o)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -o {nick}"))
            deop_menu.addAction("Half-Op (-h)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -h {nick}"))
            deop_menu.addAction("Voice (-v)").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} -v {nick}"))
            
            menu.addSeparator()
            
            # Kick/Ban actions
            menu.addAction("Kick").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"KICK {self.current_target} {nick}"))
            menu.addAction("Kick with Reason...").triggered.connect(lambda: self.kick_with_reason(nick))
            menu.addAction("Ban").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"MODE {self.current_target} +b {nick}!*@*"))
            menu.addAction("Kick + Ban").triggered.connect(lambda: (
                self.clients[self.current_nw].send_command(f"MODE {self.current_target} +b {nick}!*@*"),
                self.clients[self.current_nw].send_command(f"KICK {self.current_target} {nick}")
            ))
            menu.addSeparator()
        
        # User actions
        menu.addAction("Ignore User").triggered.connect(lambda: self.on_message(self.current_nw, self.current_target, f"*** Ignoring {nick} (not yet implemented)"))
        menu.addAction("Copy Nickname").triggered.connect(lambda: QApplication.clipboard().setText(nick))
            
        # Advanced operator commands
        try:
            self._add_oper_menu(menu, nick)
        except Exception:
            pass
        
        menu.exec_(self.chat.mapToGlobal(pos))
    
    def kick_with_reason(self, nick):
        """Prompt for kick reason and execute kick."""
        from PyQt5.QtWidgets import QInputDialog
        reason, ok = QInputDialog.getText(self, "Kick User", f"Reason for kicking {nick}:")
        if ok and self.current_nw and self.current_target:
            cmd = f"KICK {self.current_target} {nick}"
            if reason.strip():
                cmd += f" :{reason}"
            self.clients[self.current_nw].send_command(cmd)

    def openNetworkListDialogue(self): NetworkListDialogue(self).exec_()

    def showEvent(self, event):
        """Ensure Network List opens on first show if configured."""
        super().showEvent(event)
        if getattr(self, '_open_network_list_on_show', False):
            self._open_network_list_on_show = False
            QTimer.singleShot(100, self.openNetworkListDialogue)

    def openSettingsDialogue(self):
        if SettingsDialogue(self, self.settings).exec_(): self.save_settings(); self.apply_theme()
