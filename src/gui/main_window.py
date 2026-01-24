"""Main window for PyeChat."""
import os
import json
import datetime
import subprocess
import shlex
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QTextBrowser, QLabel, QMenu, 
                             QTreeWidget, QTreeWidgetItem, QApplication, 
                             QSplitter, QSizePolicy)
from PyQt5.QtGui import QIcon, QTextCursor, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer

from src.irc.irc_client import IRCClient
from src.gui.utils.colors import get_nick_colour
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

        # Load scripts/plugins
        self.plugin_loader = PluginLoader(self)
        QTimer.singleShot(500, self.plugin_loader.load_all)

        if not self.settings.get("skip_network_list", False):
            QTimer.singleShot(NETWORK_LIST_DELAY_MS, self.openNetworkListDialogue)

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
        
        style = f"""
            QMainWindow, QDialog {{ background-color: {bg}; color: {fg}; }}
            QTextBrowser {{ background-color: {bg}; color: {fg}; border: none; }}
            QPlainTextEdit {{ background-color: {s.get('input_bg', '#3c3c3c')}; color: {s.get('input_fg', '#ffffff')}; border: 1px solid {s.get('input_border', '#cccccc')}; }}
            QTreeWidget {{ background-color: {tree_bg}; color: {tree_fg}; border: none; }}
            QListWidget {{ background-color: {nick_bg}; color: {nick_fg}; border: none; }}
            QLabel#topic {{ background-color: {s.get('topic_bg', '#333333')}; color: {s.get('topic_fg', '#ffffff')}; padding: 4px; }}
            QSplitter::handle {{ background-color: {s.get('border_colour', '#cccccc')}; }}
        """
        self.setStyleSheet(style)

    def setup_ui(self):
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        self.tree = QTreeWidget()
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
        self.topic.setMinimumWidth(0)
        self.topic.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        
        self.chat = QTextBrowser()
        self.chat.setReadOnly(True)
        self.chat.setOpenExternalLinks(True)
        
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
        self.setup_buffer(nw, target)
        
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
        if txt.startswith('/'):
            parts = txt[1:].split(' ', 1)
            cmd, args = parts[0].upper(), parts[1] if len(parts) > 1 else ""
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
            else: c.send_command(txt[1:])
        elif self.current_target:
            c.send_command(f"PRIVMSG {self.current_target} :{txt}")
            self.on_message(self.current_nw, self.current_target, f"<{c.nickname}> {txt}")
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
        menu.exec_(self.tree.mapToGlobal(pos))

    def on_nick_context_menu(self, pos):
        item = self.nicks.itemAt(pos)
        if not item: return
        menu = QMenu()
        nick = item.text().lstrip(''.join(NICK_PREFIXES) + ' ')
        menu.addAction("Whois").triggered.connect(lambda: self.clients[self.current_nw].send_command(f"WHOIS {nick} {nick}"))
        menu.addAction("Query").triggered.connect(lambda: self.switch_buffer(self.current_nw, nick))
        menu.exec_(self.nicks.mapToGlobal(pos))

    def openNetworkListDialogue(self): NetworkListDialogue(self).exec_()
    def openSettingsDialogue(self):
        if SettingsDialogue(self, self.settings).exec_(): self.save_settings(); self.apply_theme()
