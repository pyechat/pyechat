def format_whois_to_irc(data, label_color="14", value_color=""):
    """
    Converts structured WHOIS data back into an IRC-formatted string with colors
    for display in the chat browser. Uses The Lounge's label-based format.
    """
    if not data: return ""
    
    t = data.get("type")
    nick = data.get("nick", "unknown")
    
    L = f"\x03{label_color}"
    V = f"\x03{value_color}" if value_color else "\x03"
    R = "\x03" # Reset
    
    if t == "user":
        return f"{L}Nickname:{R} {V}{nick}\n{L}Host mask:{R} {V}{data['user']}@{data['host']}\n{L}Real name:{R} {V}{data['realname']}"
    elif t == "server":
        return f"{L}Connected to:{R} {V}{data['server']} ({data['info']})"
    elif t == "idle":
        # Convert seconds to HH:MM:SS
        idle_secs = data['idle']
        hours = idle_secs // 3600
        minutes = (idle_secs % 3600) // 60
        seconds = idle_secs % 60
        idle_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        msg = f"{L}Idle since:{R} {V}{idle_formatted}"
        if data.get('signon'):
            msg += f", {L}signon:{R} {V}{data['signon']}"
        return msg
    elif t == "status":
        return f"{L}Registered nick:{R} {V}{data['info']}"
    elif t == "bot":
        return f"{L}Bot status:{R} {V}{data['info']}"
    elif t == "channels":
        return f"{L}Channels:{R} {V}{data['channels']}"
    elif t == "account":
        return f"{L}Logged in as:{R} {V}{data['account']}"
    elif t == "away":
        return f"{L}Away message:{R} {V}{data['message']}"
    elif t == "ircop":
        return f"{L}IRC Operator:{R} {V}{data['privs']}"
    elif t == "realhost":
        return f"{L}Actual host:{R} {V}{data['info']}"
    elif t == "modes":
        return f"{L}Modes:{R} {V}{data['modes']}"
    elif t == "ssl_fingerprint":
        return f"{L}SSL Fingerprint:{R} {V}{data['fingerprint']}"
    elif t == "secure":
        return f"{L}Secure connection:{R} {V}Yes"
    elif t == "country":
        return f"{L}Country:{R} {V}{data['country']}"
    elif t == "end":
        return f"{L}End of WHOIS"
    
    return ""
