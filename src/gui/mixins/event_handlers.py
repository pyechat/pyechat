import datetime
from src.gui.utils.colors import get_nick_colour
from src.gui.utils.formatters import irc_to_html, format_text_event
from src.gui.utils.whois import format_whois_to_irc

NICK_PREFIXES = ('~', '&', '@', '%', '+')
NICK_RANK_MODES = {'o': '@', 'v': '+', 'h': '%', 'a': '&', 'q': '~'}

# Standard mIRC control codes for constructing event strings
C = {
    'WHITE': '\x0300', 'BLACK': '\x0301', 'BLUE': '\x0302', 'GREEN': '\x0303',
    'RED': '\x0304', 'BROWN': '\x0305', 'PURPLE': '\x0306', 'ORANGE': '\x0307',
    'YELLOW': '\x0308', 'TEAL': '\x0310', 'CYAN': '\x0311', 'LIGHT_BLUE': '\x0312',
    'PINK': '\x0313', 'GREY': '\x0314', 'PLAIN': '\x0f'
}

class EventHandlerMixin:
    def _should_filter_join_part(self, nw, command, sender, target):
        """Check if join/part/quit event should be filtered based on smart filtering settings."""
        # If completely hidden, return True
        if self.settings.get("hide_join_part", False) and command in ("JOIN", "PART", "QUIT"):
            return True
        
        # If smart filtering is disabled, show all events
        if not self.settings.get("smart_filter_join_part", True):
            return False
        
        # Don't filter our own join/part
        if nw in self.clients and sender.lower() == self.clients[nw].nickname.lower():
            return False
        
        # Smart filtering: hide if user hasn't spoken recently
        filter_seconds = self.settings.get("smart_filter_seconds", 300)
        key = (nw, target, sender)
        
        now = datetime.datetime.now()
        last_activity = self.recent_activity.get(key)
        
        if last_activity:
            time_diff = (now - last_activity).total_seconds()
            # If user spoke within the filter window, show the join/part
            if time_diff < filter_seconds:
                return False
        
        # Filter out the event (user hasn't been active)
        return True
    
    def _track_user_activity(self, nw, target, sender):
        """Track when a user last spoke in a channel."""
        if not target:
            return
        key = (nw, target, sender)
        self.recent_activity[key] = datetime.datetime.now()
    
    def on_event_received(self, nw, command, sender, args, tags):
        events = self.settings.get("events_v2", {})
        
        # Check if this event should be filtered
        target = args[0] if args else ""
        if command in ("JOIN", "PART", "QUIT"):
            if self._should_filter_join_part(nw, command, sender, target):
                # Still process side effects even if we don't display the message
                if command == "JOIN" and sender.lower() == self.clients[nw].nickname.lower():
                    self.setup_buffer(nw, target)
                    if not self.find_item(nw, target): self.add_tree_item(nw, target)
                    if not self.current_target: self.switch_buffer(nw, target)
                return
        
        # Fallback for core events if they are not explicitly customised
        if command not in events:
            self._handle_fallback_event(nw, command, sender, args, tags)
            return

        data = events[command]
        fmt = data.get("fmt", "") if isinstance(data, dict) else data
        clr_hex = data.get("colour", "") if isinstance(data, dict) else ""
        
        if not fmt: return
        
        # Build the context for variable replacement
        ctx = self._build_event_context(nw, command, sender, args, tags)
        
        # If MODE targets a user (not a channel), show it in network status rather than creating a per-user buffer
        if command == "MODE":
            ch = ctx.get('channel', '')
            if not (ch.startswith('#') or ch.startswith('&')):
                ctx['target'] = ''
                ctx['channel'] = ''
        
        try:
            if '$' in fmt:
                # Custom handler for HexChat style variables ($1, $2, etc)
                msg_text = format_text_event(fmt, self._get_numeric_args(command, sender, args, tags))
            else:
                # Python string format handler
                msg_text = fmt.format(**ctx)
                
            tags["fmt_color"] = clr_hex
            
            # Handle side-effects (like joining a channel self also means opening a buffer)
            if command == "JOIN" and sender.lower() == self.clients[nw].nickname.lower():
                target = args[0]
                self.setup_buffer(nw, target)
                if not self.find_item(nw, target): self.add_tree_item(nw, target)
                if not self.current_target: self.switch_buffer(nw, target)
            
            for line in msg_text.split('\n'):
                if line.strip():
                    self.on_message(nw, ctx.get('target', ''), line, tags)
                    
        except Exception as e:
            # Silently log format errors to avoided flooding the UI
            print(f"Error formatting event '{command}': {e}")

    def _handle_fallback_event(self, nw, command, sender, args, tags):
        """Default display logic for core events when no theme is present."""
        if command == "JOIN":
            target = args[0]
            self.on_message(nw, target, f"*** {sender} ({tags.get('host', 'unknown')}) has joined {target}")
        elif command == "PART":
            target = args[0]
            reason = f" ({args[1]})" if len(args) > 1 else ""
            self.on_message(nw, target, f"*** {sender} has left {target}{reason}")
        elif command == "QUIT":
            reason = f" ({args[0]})" if args else ""
            for k in [k for k in self.buffers if k[0] == nw and k[1]]:
                self.on_message(nw, k[1], f"*** {sender} has quit{reason}")
        elif command == "NICK":
            self.on_message(nw, "", f"*** {sender} is now known as {args[0]}")
        elif command == "KICK":
            chan, target, reason = args[0], args[1], f" ({args[2]})" if len(args) > 2 else ""
            self.on_message(nw, chan, f"*** {target} was kicked by {sender}{reason}")
        elif command == "MODE":
            chan, mode = args[0], args[1]
            # If MODE applies to a channel, show it in the channel; otherwise, show it in the network status buffer
            target = chan if chan.startswith(('#', '&')) else ""
            self.on_message(nw, target, f"*** {sender} sets mode: {mode}")

    def _build_event_context(self, nw, command, sender, args, tags):
        """Constructs the dictionary used for string formatting."""
        target = args[0] if args else ""
        # Adjust target based on event type
        if command in ("QUIT", "NICK"): target = ""
        if command == "NOTICE" and len(args) > 0 and args[0].lower() == self.clients[nw].nickname.lower(): target = sender
        if command == "INVITE" and len(args) > 1: target = "" # Invites are usually global notices
        
        mode_str = " ".join(args[1:]) if command == "MODE" and len(args) > 1 else ""
        
        return {
            "nick": sender, "sender": sender, "host": tags.get('host', ''),
            "channel": target, "target": target,
            "msg": args[-1] if args else "", "reason": args[-1] if args else "",
            "mode": mode_str,
            "kicker": sender if command == "KICK" else "",
            "old_nick": sender if command == "NICK" else "",
            "new_nick": args[0] if command == "NICK" else "",
            
            # Colour helpers
            "white": C['WHITE'], "black": C['BLACK'], "blue": C['BLUE'], "green": C['GREEN'],
            "red": C['RED'], "brown": C['BROWN'], "purple": C['PURPLE'], "orange": C['ORANGE'],
            "yellow": C['YELLOW'], "teal": C['TEAL'], "cyan": C['CYAN'], "light_blue": C['LIGHT_BLUE'],
            "pink": C['PINK'], "grey": C['GREY'], "plain": C['PLAIN'], 
            
            # Short aliases
            "n": sender, "h": tags.get('host', ''), "c": target, "m": args[-1] if args else ""
        }

    def _get_numeric_args(self, command, sender, args, tags):
        """Helper to map args for $1, $2 style replacement."""
        if command == "JOIN": return [sender, args[0], tags.get('host', '')]
        if command == "PART": return [sender, tags.get('host', ''), args[0], args[1] if len(args) > 1 else ""]
        if command == "QUIT": return [sender, args[0] if args else "", tags.get('host', '')]
        if command == "KICK": return [sender, args[1], args[0], args[2] if len(args) > 2 else ""]
        if command == "NICK": return [sender, args[0]]
        if command == "MODE": return [sender, " ".join(args[1:]) if len(args) > 1 else "", args[0]]
        if command == "NOTICE": return [sender, args[1]]
        if command == "INVITE": return [args[1], sender]
        if command.isdigit(): return args[1:] if len(args) > 1 else args
        return args

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
                    if self.current_nw == nw and self.current_target == k[1]:
                        refresh_needed = True
                    break
        
        if refresh_needed:
            self.nick_update_queued.add((self.current_nw, self.current_target))
            if not self.nick_timer.isActive():
                self.nick_timer.start(100)

    def on_kick(self, nw, chan, target, kicker, reason):
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
        
        # Mode messages are formatted and displayed via the generic event handler
        # (on_event_received) so avoid double-posting here. We still update nick
        # prefixes and refresh the nick list above.
        pass
        
        if self.current_nw == nw and self.current_target == chan:
            self.nick_update_queued.add((nw, chan))
            if not self.nick_timer.isActive():
                self.nick_timer.start(100)

    def on_notice(self, nw, target, sender, msg):
        pass

    def on_invite(self, nw, chan, sender, nick):
        pass

    def on_action(self, nw, target, sender, msg):
        route_to = target if target.startswith('#') or target.startswith('&') else sender
        self.on_message(nw, route_to, f"* {sender} {msg}")

    def on_topic(self, nw, chan, topic):
        self.setup_buffer(nw, chan)
        self.add_tree_item(nw, chan)
        self.buffers[(nw, chan)]["topic"] = topic
        # Also post a message into the channel buffer so it's visible in the chat window when joining
        try:
            if topic:
                self.on_message(nw, chan, f"*** Topic for {chan}: {topic}")
        except Exception:
            pass
        if self.current_nw == nw and self.current_target == chan:
            # Compose label including topic and any metadata
            t = topic or chan
            meta = self.buffers[(nw, chan)].get("topic_meta")
            if meta:
                setter = meta.get("setter")
                ts = meta.get("set_at")
                try:
                    ts_text = datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M') if ts else ""
                    if setter and ts_text:
                        t = f"{t} — set by {setter} at {ts_text}"
                except Exception:
                    pass
            self.topic.setText(t)
            self.topic.setToolTip(topic)

    def on_topic_meta(self, nw, chan, setter, ts):
        """Handle topic setter/time info (RPL_TOPICWHOTIME)."""
        self.setup_buffer(nw, chan)
        self.add_tree_item(nw, chan)
        self.buffers[(nw, chan)]["topic_meta"] = {"setter": setter, "set_at": ts}
        # Post a message into the channel describing who set the topic and when
        try:
            if setter and ts:
                ts_text = datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M')
                self.on_message(nw, chan, f"*** Topic set by {setter} at {ts_text}")
        except Exception:
            pass
        if self.current_nw == nw and self.current_target == chan:
            # Re-render the topic label to include meta
            topic_text = self.buffers[(nw, chan)].get("topic") or chan
            try:
                ts_text = datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M')
                if setter and ts_text:
                    topic_text = f"{topic_text} — set by {setter} at {ts_text}"
            except Exception:
                pass
            self.topic.setText(topic_text)
            self.topic.setToolTip(self.buffers[(nw, chan)].get("topic") or chan)
