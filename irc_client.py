import socket
import time
from logger import Logger
from PyQt5.QtCore import QThread, pyqtSignal

class IRCClient(QThread):
    new_message = pyqtSignal(str)
    joined_channel = pyqtSignal(str)
    sent_command = pyqtSignal(str)

    def __init__(self, server, port, nick, channel):
        super().__init__()
        self.server = server
        self.port = port
        self.nick = nick
        self.channel = channel
        self.logger = Logger('logs/elitebot.log')

    def decode(self, bytes):
        try: 
            text = bytes.decode('utf-8')
        except UnicodeDecodeError:
            try: 
                text = bytes.decode('latin1')
            except UnicodeDecodeError:
                try: 
                    text = bytes.decode('iso-8859-1')
                except UnicodeDecodeError:
                    text = bytes.decode('cp1252')
        return text

    def parse_message(self, message):
        parts = message.split()
        if not parts:
            return None, None, []
        source = parts[0][1:] if parts[0].startswith(':') else None
        command = parts[1] if source else parts[0]
        args_start = 2 if source else 1
        args = []
        trailing_arg_start = None
        for i, part in enumerate(parts[args_start:], args_start):
            if part.startswith(':'):
                trailing_arg_start = i
                break
            else:
                args.append(part)
        if trailing_arg_start is not None:
            args.append(' '.join(parts[trailing_arg_start:])[1:])
        return source, command, args

    def ircsend(self, msg):
        try:
            if msg != '':
                self.logger.info(f'Sending command: {msg}')
                self.ircsock.send(bytes(f'{msg}\r\n','UTF-8'))
        except Exception as e:
            self.logger.error(f'Error sending IRC message: {e}')
            raise

    def run(self):
        self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ircsock.connect((self.server, self.port))
        self.ircsend(f"USER {self.nick} {self.nick} {self.nick} :This is a fun bot!")
        self.ircsend(f"NICK {self.nick}")

        while True:
            ircmsg = self.ircsock.recv(2048)
            ircmsg = self.decode(ircmsg)
            
            # Check for different line endings and split accordingly
            if '\r\n' in ircmsg:
                messages = ircmsg.split('\r\n')
            elif '\n' in ircmsg:
                messages = ircmsg.split('\n')
            else:
                messages = [ircmsg]

            for message in messages:
                if message:  # Ignore empty lines
                    message = message.strip()
                    source, command, args = self.parse_message(message)
                    self.logger.debug(f'Received: source: {source} | command: {command} | args: {args}')
                    self.new_message.emit(message)

                    if command == 'PRIVMSG':
                        channel, message = args[0], args[1]
                        source_nick = source.split('!')[0]
                        if message.startswith('&'):
                            cmd, *cmd_args = message[1:].split()
                            self.handle_command(source_nick, channel, cmd, cmd_args)
                        for plugin in self.plugins:
                            plugin.handle_message(source_nick, channel, message)

                    elif command == 'PING':
                        nospoof = args[0][1:] if args[0].startswith(':') else args[0]
                        self.ircsend(f'PONG :{nospoof}')

                    if message.endswith("End of /MOTD command."):
                        self.ircsend(f'JOIN {self.channel}')
                        self.joined_channel.emit(self.channel)

            time.sleep(0.1)
