def format_whois_to_irc(data):
    """
    Converts structured WHOIS data back into an IRC-formatted string with colors
    for display in the chat browser.
    """
    if not data: return ""
    
    t = data.get("type")
    nick = data.get("nick", "unknown")
    
    if t == "user":
        return f"\x0312* [{nick}] ({data['user']}@{data['host']}): {data['realname']}\x03"
    elif t == "server":
        return f"\x0312* [{nick}]\x03 \x0304{data['server']}\x03 \x0312:{data['info']}\x03"
    elif t == "idle":
        msg = f"\x0312* [{nick}] idle {data['idle']}s"
        if data.get('signon'):
            msg += f", signed on at {data['signon']}"
        return msg + "\x03"
    elif t == "status":
        return f"\x0312* [{nick}] {data['info']}\x03"
    elif t == "bot":
        return f"\x0312* [{nick}] {data['info']}\x03"
    elif t == "channels":
        return f"\x0312* [{nick}] {data['channels']}\x03"
    elif t == "account":
        return f"\x0312* [{nick}] {data['info']} {data['account']}\x03"
    elif t == "away":
        return f"\x0312* [{nick}] is away: {data['message']}\x03"
    elif t == "ircop":
        return f"\x0312* [{nick}] {data['privs']}\x03"
    elif t == "realhost":
        return f"\x0312* [{nick}] {data['info']}\x03"
    elif t == "modes":
        return f"\x0312* [{nick}] {data['modes']}\x03"
    elif t == "ssl_fingerprint":
        return f"\x0312* [{nick}] SSL Fingerprint: {data['fingerprint']}\x03"
    elif t == "secure":
        return f"\x0312* [{nick}] {data['info']}\x03"
    elif t == "country":
        return f"\x0312* [{nick}] is connecting from {data['country']}\x03"
    elif t == "end":
        return f"\x0312* [{nick}] {data['message']}\x03"
    
    return ""
