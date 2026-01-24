from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtNetwork import QSslSocket
from src.irc.logger import Logger
import base64
from src.irc.whois import parse_whois_numeric
import datetime

class IRCClient(QObject):
    received_message = pyqtSignal(str, str, dict)
    received_nick_list = pyqtSignal(tuple)
    received_topic = pyqtSignal(str, str)
    connected_to_server = pyqtSignal(str)
    disconnected_from_server = pyqtSignal(str)
    parted_channel = pyqtSignal(str, str)
    nick_changed = pyqtSignal(str, str)
    received_kick = pyqtSignal(str, str, str, str)
    received_mode = pyqtSignal(str, str, str)
    received_notice = pyqtSignal(str, str, str)
    received_invite = pyqtSignal(str, str, str)
    received_action = pyqtSignal(str, str, str)
    received_quit = pyqtSignal(str, str)
    received_whois = pyqtSignal(dict, dict)
    event_received = pyqtSignal(str, str, list, dict)

    def __init__(self, network_name, server, port, nickname, realname, auto_join_channels=None, use_ssl=False, password=None, auto_reconnect=True, sasl_method=None, sasl_user=None, sasl_pass=None, auto_commands=None):
        super().__init__()
        self.socket = QSslSocket()
        self.socket.readyRead.connect(self.on_ready_read)
        self.socket.errorOccurred.connect(self.on_error_occurred)
        self.socket.connected.connect(self.start_encryption)
        self.socket.encrypted.connect(self.on_socket_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.sslErrors.connect(self.on_ssl_errors)
        
        self.network_name = network_name
        self.server = server
        self.port = port
        self.nickname = nickname
        self.realname = realname
        self.auto_join_channels = auto_join_channels or []
        self.use_ssl = use_ssl
        self.password = password
        self.auto_reconnect = auto_reconnect
        self.sasl_method = sasl_method
        self.sasl_user = sasl_user
        self.sasl_pass = sasl_pass
        self.auto_commands = auto_commands or []
        
        self.is_registered = False
        self.capabilities = ["server-time", "multi-prefix", "away-notify", "account-notify", "extended-join"]
        if self.sasl_method:
            self.capabilities.append("sasl")

        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.send_ping)
        self.ping_timer.start(60000)
        
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.connect_to_host)
        
        self.logger = Logger('logs/irc_client.log')

    def start_encryption(self):
        if self.use_ssl: self.socket.startClientEncryption()
        else: self.on_socket_connected()

    def on_socket_connected(self):
        self.reconnect_timer.stop()
        self.send_command('CAP LS 302')
        if self.password:
            self.send_command(f'PASS {self.password}')
        self.send_command(f'NICK {self.nickname}')
        self.send_command(f'USER {self.nickname} 0 * :{self.realname}')

    def connect_to_host(self):
        if self.socket.state() != QSslSocket.UnconnectedState:
            self.socket.abort()
        
        self.logger.info(f"Connecting to {self.server}:{self.port}")
        if self.use_ssl:
            self.socket.connectToHostEncrypted(self.server, self.port)
        else:
            self.socket.connectToHost(self.server, self.port)

    def on_disconnected(self):
        self.is_registered = False
        self.disconnected_from_server.emit(self.network_name)
        if self.auto_reconnect:
            self.logger.info("Connection lost. Retrying in 5 seconds...")
            self.reconnect_timer.start(5000)

    def decode(self, bytes_data):
        for enc in ['utf-8', 'latin1', 'cp1252']:
            try: return bytes_data.decode(enc)
            except: continue
        return bytes_data.decode('utf-8', errors='replace')

    def parse_message(self, message):
        tags = {}
        if message.startswith('@'):
            try:
                tags_str, message = message[1:].split(' ', 1)
                for tag in tags_str.split(';'):
                    if '=' in tag:
                        key, val = tag.split('=', 1)
                        val = val.replace('\\:', ';').replace('\\s', ' ').replace('\\\\', '\\').replace('\\r', '\r').replace('\\n', '\n')
                        tags[key] = val
                    else:
                        tags[tag] = True
            except: pass

        parts = message.split()
        if not parts: return tags, None, None, []
        source = parts[0][1:] if parts[0].startswith(':') else None
        command = parts[1] if source else parts[0]
        args_start = 2 if source else 1
        args = []
        trailing = None
        for i, part in enumerate(parts[args_start:], args_start):
            if part.startswith(':'):
                trailing = ' '.join(parts[i:])[1:]
                break
            args.append(part)
        if trailing is not None: args.append(trailing)
        return tags, source, command, args

    @pyqtSlot()
    def on_ready_read(self):
        while self.socket.canReadLine():
            line = self.decode(self.socket.readLine().data()).strip()
            tags, source, command, args = self.parse_message(line)
            if not command: continue

            sender = self.server
            if source:
                if '!' in source:
                    sender = source.split('!')[0]
                    tags['host'] = source.split('!', 1)[1]
                else:
                    sender = source

            if command != 'PRIVMSG' and not command.isdigit():
                self.event_received.emit(command, sender, args, tags)
            
            if command == 'PING':
                self.send_command(f'PONG :{args[0]}')
            
            elif command == 'CAP':
                sub_cmd = args[1]
                if sub_cmd == 'LS':
                    supported = args[2].split()
                    to_req = [cap for cap in self.capabilities if cap in supported]
                    if to_req: self.send_command(f"CAP REQ :{' '.join(to_req)}")
                    else: self.send_command('CAP END')
                elif sub_cmd == 'ACK':
                    if 'sasl' in args[2]:
                        self.send_command(f'AUTHENTICATE {self.sasl_method}')
                    else:
                        self.send_command('CAP END')
                elif sub_cmd == 'NAK':
                    self.send_command('CAP END')

            elif command == 'AUTHENTICATE':
                if args[0] == '+':
                    if self.sasl_method == 'PLAIN':
                        auth_str = f"{self.sasl_user}\0{self.sasl_user}\0{self.sasl_pass}"
                        b64_auth = base64.b64encode(auth_str.encode()).decode()
                        self.send_command(f'AUTHENTICATE {b64_auth}')
                    elif self.sasl_method == 'EXTERNAL':
                        self.send_command('AUTHENTICATE +')
            
            elif command == '903':
                self.received_message.emit("", "*** SASL authentication successful", tags)
                self.send_command('CAP END')
            
            elif command in ['904', '905', '907']:
                self.received_message.emit("", f"*** SASL authentication failed ({command})", tags)
                self.send_command('CAP END')

            elif command == '001':
                self.is_registered = True
                self.nickname = args[0]
                self.received_message.emit("", f"*** Connected to {self.server}", tags)
                self.connected_to_server.emit(self.network_name)
                for cmd in self.auto_commands: self.send_command(cmd)
                for chan in self.auto_join_channels: self.send_command(f'JOIN {chan}')

            elif command == 'PRIVMSG':
                target, msg = args[0], args[1]
                if msg.startswith('\x01') and msg.endswith('\x01'):
                    self.handle_ctcp(sender, target, msg[1:-1])
                else:
                    route_to = sender if target.lower() == self.nickname.lower() else target
                    self.received_message.emit(route_to, f'<{sender}> {msg}', tags)

            elif command == 'NOTICE':
                target, msg = args[0], args[1]
                self.received_notice.emit(target, sender, msg)

            elif command == 'INVITE':
                invited_nick, chan = args[0], args[1]
                self.received_invite.emit(chan, sender, invited_nick)

            elif command == 'JOIN':
                chan = args[0]
                self.received_nick_list.emit((chan, sender))

            elif command == 'PART':
                chan = args[0]
                self.parted_channel.emit(chan, sender)

            elif command == 'QUIT':
                reason = args[0] if args else "Quit"
                self.received_quit.emit(sender, reason)

            elif command == 'NICK':
                new_nick = args[0]
                if sender == self.nickname: self.nickname = new_nick
                self.nick_changed.emit(sender, new_nick)

            elif command == 'KICK':
                chan, target, reason = args[0], args[1], args[2] if len(args) > 2 else ""
                self.received_kick.emit(chan, target, sender, reason)

            elif command == 'MODE':
                chan, mode = args[0], " ".join(args[1:])
                self.received_mode.emit(chan, sender, mode)

            elif command == '332':
                self.received_topic.emit(args[1], args[2])

            elif command == '353':
                chan = args[2]
                for n in args[3].split():
                    self.received_nick_list.emit((chan, n))

            elif command.isdigit():
                try:
                    whois_data = parse_whois_numeric(command, args)
                    if whois_data:
                        self.received_whois.emit(whois_data, tags)
                    
                    self.event_received.emit(command, sender, args, tags)
                    
                    if not whois_data and command not in ['332', '353', '001']:
                        text = " ".join(args[1:]) if len(args) > 1 else (args[0] if args else "")
                        self.received_message.emit("", f"[{command}] {text}", tags)
                except Exception:
                    text = " ".join(args[1:]) if len(args) > 1 else (args[0] if args else "")
                    self.received_message.emit("", f"[{command}] {text}", tags)

    def handle_ctcp(self, sender, target, payload):
        parts = payload.split(' ', 1)
        command = parts[0].upper()
        if command == 'VERSION':
            self.send_command(f'NOTICE {sender} :\x01VERSION PyeChat 1.0 (PyQt5)\x01')
        elif command == 'PING':
            ts = parts[1] if len(parts) > 1 else ""
            self.send_command(f'NOTICE {sender} :\x01PING {ts}\x01')
        elif command == 'TIME':
            now = datetime.datetime.now().ctime()
            self.send_command(f'NOTICE {sender} :\x01TIME {now}\x01')
        elif command == 'ACTION':
            msg = parts[1] if len(parts) > 1 else ""
            self.received_action.emit(target, sender, msg)

    def send_ping(self):
        if self.socket.state() == QSslSocket.ConnectedState:
            self.send_command(f'PING :{self.server}')

    def send_command(self, command):
        if self.socket.state() == QSslSocket.ConnectedState:
            self.socket.write(f'{command}\r\n'.encode())

    @pyqtSlot('QList<QSslError>')
    def on_ssl_errors(self, errors):
        for err in errors:
            self.logger.warning(f"SSL Error: {err.errorString()}")
        self.socket.ignoreSslErrors()

    @pyqtSlot(QSslSocket.SocketError)
    def on_error_occurred(self, socket_error):
        err = self.socket.errorString()
        if self.socket.state() == QSslSocket.UnconnectedState:
            self.received_message.emit("", f"*** Connection Error: {err}", {})
        self.logger.error(f"Socket Error: {err}")
