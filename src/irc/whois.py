import datetime

def parse_whois_numeric(command, args):
    """
    Parses WHOIS numeric replies and returns a structured dictionary.
    Returns None if the command is not a WHOIS numeric we handle.
    """
    try:
        if command == '311': # WHOIS User
            return {
                "type": "user",
                "nick": args[1],
                "user": args[2],
                "host": args[3],
                "realname": args[5]
            }
        elif command == '312': # WHOIS Server
            return {
                "type": "server",
                "nick": args[1],
                "server": args[2],
                "info": args[3]
            }
        elif command == '317': # WHOIS Idle/Signon
            nick, idle = args[1], int(args[2])
            signon = None
            if len(args) > 3:
                try:
                    ts = int(args[3])
                    if ts > 0:
                        signon = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                except: pass
            return {
                "type": "idle",
                "nick": nick,
                "idle": idle,
                "signon": signon
            }
        elif command in ['307', '320']: # Registered / Status
            return {
                "type": "status",
                "nick": args[1],
                "info": args[2] if len(args) > 2 else "has identified for this nick"
            }
        elif command in ['335', '310']: # Bot / HelpOp
            return {
                "type": "bot",
                "nick": args[1],
                "info": args[2] if len(args) > 2 else "is a bot"
            }
        elif command == '319': # WHOIS Channels
            return {
                "type": "channels",
                "nick": args[1],
                "channels": args[2]
            }
        elif command == '330': # WHOIS Logged In
            return {
                "type": "account",
                "nick": args[1],
                "account": args[2],
                "info": args[3] if len(args) > 3 else "is logged in as"
            }
        elif command == '301': # AWAY
            return {
                "type": "away",
                "nick": args[1],
                "message": args[2]
            }
        elif command == '313': # WHOIS IRCop
            return {
                "type": "ircop",
                "nick": args[1],
                "privs": args[2]
            }
        elif command in ['378', '338']: # WHOIS IP/Host (Real)
            return {
                "type": "realhost",
                "nick": args[1],
                "info": args[2] if len(args) > 2 else args[-1]
            }
        elif command == '379': # WHOIS Modes
            return {
                "type": "modes",
                "nick": args[1],
                "modes": " ".join(args[2:])
            }
        elif command == '275': # WHOIS SSL Cert Fingerprint
            return {
                "type": "ssl_fingerprint",
                "nick": args[1],
                "fingerprint": args[2]
            }
        elif command in ['671', '276']: # WHOIS SSL/TLS / Secure
            return {
                "type": "secure",
                "nick": args[1],
                "info": args[2] if len(args) > 2 else "is using a secure connection"
            }
        elif command == '344': # WHOIS Country
            return {
                "type": "country",
                "nick": args[1],
                "country": args[2]
            }
        elif command == '318': # End of WHOIS
            return {
                "type": "end",
                "nick": args[1],
                "message": "End of WHOIS list."
            }
    except Exception:
        pass
    return None
