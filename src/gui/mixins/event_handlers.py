import datetime
from src.gui.utils.colors import get_nick_colour
from src.gui.utils.formatters import irc_to_html, format_text_event
from src.gui.utils.whois import format_whois_to_irc

NICK_PREFIXES = ('~', '&', '@', '%', '+')
NICK_RANK_MODES = {'o': '@', 'v': '+', 'h': '%', 'a': '&', 'q': '~'}

class EventHandlerMixin:
    def on_event_received(self, nw, command, sender, args, tags):
        events = self.settings.get("events_v2", {})
        if command not in events: return
        data = events[command]
        fmt = data["fmt"] if isinstance(data, dict) else data
        clr_hex = data.get("colour", "") if isinstance(data, dict) else ""
        if not fmt: return
        
        host = tags.get('host', '')
        evt_args = []
        target = ""
        mode_str = ""

        if command == "JOIN":
            target = args[0]
            evt_args = [sender, target, host]
        elif command == "PART":
            target = args[0]
            reason = args[1] if len(args) > 1 else ""
            evt_args = [sender, host, target, reason]
        elif command == "QUIT":
            reason = args[0] if args else ""
            evt_args = [sender, reason, host]
        elif command == "KICK":
            target = args[0]
            kicked = args[1]
            reason = args[2] if len(args) > 2 else ""
            evt_args = [sender, kicked, target, reason]
            if kicked.lower() == self.clients[nw].nickname.lower():
                msg = f"* You have been kicked from {target} by {sender} ({reason})"
                self.on_message(nw, target, msg, tags)
                return
        elif command == "NICK":
            new_nick = args[0]
            evt_args = [sender, new_nick]
        elif command == "MODE":
            target = args[0]
            mode_str = " ".join(args[1:]) if len(args) > 1 else ""
            evt_args = [sender, mode_str, target]
        elif command == "NOTICE":
            target = args[0]
            msg = args[1]
            evt_args = [sender, msg]
            if target.lower() == self.clients[nw].nickname.lower(): target = sender
        elif command == "INVITE":
            target = ""
            chan = args[1]
            evt_args = [chan, sender]
        elif command.isdigit():
            evt_args = args[1:] if len(args) > 1 else args
        
        try:
            if '$' in fmt:
                msg = format_text_event(fmt, evt_args)
            else:
                ctx = {
                    "nick": sender, "sender": sender, "host": host,
                    "channel": target, "target": target,
                    "msg": args[-1] if args else "", "reason": args[-1] if args else "",
                    "mode": mode_str if command == "MODE" else "",
                    "kicker": sender if command == "KICK" else "",
                    "old_nick": sender if command == "NICK" else "",
                    "new_nick": args[0] if command == "NICK" else "",
                    "white": "\x0300", "black": "\x0301", "blue": "\x0302", "green": "\x0303",
                    "red": "\x0304", "brown": "\x0305", "purple": "\x0306", "orange": "\x0307",
                    "yellow": "\x0308", "teal": "\x0310", "cyan": "\x0311", "light_blue": "\x0312",
                    "pink": "\x0313", "grey": "\x0314", "plain": "\x0f", "c23": "\x0323",
                    "n": sender, "h": host, "c": target, "m": args[-1] if args else ""
                }
                msg = fmt.format(**ctx)
                
            tags["fmt_color"] = clr_hex
            
            if command == "JOIN" and sender.lower() == self.clients[nw].nickname.lower():
                self.setup_buffer(nw, target)
                if not self.find_item(nw, target): self.add_tree_item(nw, target)
                if not self.current_target: self.switch_buffer(nw, target)
            
            for line in msg.split('\n'):
                if line.strip():
                    self.on_message(nw, target, line, tags)
        except Exception as e:
            print(f"Event formatting error for {command}: {e}")

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

    def on_whois(self, nw, data, tags):
        whois_type_to_numeric = {
            "user": "311", "server": "312", "idle": "317",
            "status": "307", "bot": "310", "channels": "319",
            "account": "330", "away": "301", "ircop": "313",
            "realhost": "378", "modes": "379", "ssl_fingerprint": "275",
            "secure": "671", "country": "344", "end": "318"
        }
        
        numeric = whois_type_to_numeric.get(data.get("type"))
        if numeric and numeric in self.settings.get("events_v2", {}):
            return
        
        msg = format_whois_to_irc(data)
        if msg:
            for line in msg.split('\n'):
                if line.strip():
                    self.on_message(nw, "", line, tags)
    
    def on_mode(self, nw, chan, sender, mode):
        self.on_event_received(nw, "MODE", sender, [chan, mode], {})
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        
        parts = mode.split()
        if len(parts) < 2: return
        flags_str = parts[0]
        args = parts[1:]
        
        if not flags_str.startswith(('+', '-')): return
        
        action = flags_str[0]
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
            elif char in "beI" or char == "k":
                arg_idx += 1
            elif char == "l" and action == "+":
                arg_idx += 1
        
        if self.current_nw == nw and self.current_target == chan:
            self.nick_update_queued.add((nw, chan))
            if not self.nick_timer.isActive():
                self.nick_timer.start(100)

    def on_notice(self, nw, target, sender, msg):
        self.on_event_received(nw, "NOTICE", sender, [target, msg], {})

    def on_invite(self, nw, chan, sender, nick):
        msg = f"*** {sender} invited {nick} to {chan}"
        self.on_message(nw, "", msg)

    def on_action(self, nw, target, sender, msg):
        self.on_event_received(nw, "ACTION", sender, [target, msg], {})

    def on_topic(self, nw, chan, topic):
        self.setup_buffer(nw, chan)
        self.add_tree_item(nw, chan)
        self.buffers[(nw, chan)]["topic"] = topic
        if self.current_nw == nw and self.current_target == chan:
            self.topic.setText(topic)
            self.topic.setToolTip(topic)
