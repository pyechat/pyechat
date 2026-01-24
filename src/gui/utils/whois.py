def format_whois_to_irc(data):
    """
    Converts structured WHOIS data back into an IRC-formatted string with colors
    for display in the chat browser. Uses The Lounge's label-based format.
    """
    if not data: return ""
    
    t = data.get("type")
    nick = data.get("nick", "unknown")
    
    if t == "user":
        return f"\x0314Host mask:\x03 {data['user']}@{data['host']}\n\x0314Real name:\x03 {data['realname']}"
    elif t == "server":
        return f"\x0314Connected to:\x03 {data['server']} ({data['info']})"
    elif t == "idle":
        # Convert seconds to HH:MM:SS
        idle_secs = data['idle']
        hours = idle_secs // 3600
        minutes = (idle_secs % 3600) // 60
        seconds = idle_secs % 60
        idle_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        msg = f"* [{nick}] idle {idle_formatted}"
        if data.get('signon'):
            msg += f", signon: {data['signon']}"
        return msg
    elif t == "status":
        return f"\x0314Registered nick:\x03 {data['info']}"
    elif t == "bot":
        return f"\x0314Bot status:\x03 {data['info']}"
    elif t == "channels":
        return f"\x0314Channels:\x03 {data['channels']}"
    elif t == "account":
        return f"\x0314Logged in as:\x03 {data['account']}"
    elif t == "away":
        return f"\x0314Away message:\x03 {data['message']}"
    elif t == "ircop":
        return f"\x0314IRC Operator:\x03 {data['privs']}"
    elif t == "realhost":
        return f"\x0314Actual host:\x03 {data['info']}"
    elif t == "modes":
        return f"\x0314Modes:\x03 {data['modes']}"
    elif t == "ssl_fingerprint":
        return f"\x0314SSL Fingerprint:\x03 {data['fingerprint']}"
    elif t == "secure":
        return f"\x0314Secure connection:\x03 Yes"
    elif t == "country":
        return f"\x0314Country:\x03 {data['country']}"
    elif t == "end":
        return f"\x0314End of WHOIS"
    
    return ""
