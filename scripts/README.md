# PyeChat Scripts

This directory contains Python and TCL scripts that are automatically loaded when PyeChat starts.

## Creating a Python Script

1. Create a `.py` file in this directory
2. Define a `setup(main_window)` function that will be called on load
3. Optionally define a `teardown(main_window)` function for cleanup

## Example Python Script

```python
def setup(main_window):
    """Called when the script is loaded."""
    print("My script loaded!")
    
    # Access IRC clients
    for network_name, client in main_window.clients.items():
        # Connect to IRC events
        client.received_message.connect(
            lambda t, m, tags, nw=network_name: handle_msg(main_window, nw, t, m)
        )

def teardown(main_window):
    """Called when the script is unloaded."""
    print("My script unloaded!")

def handle_msg(main_window, network, target, message):
    """Handle incoming messages."""
    if "keyword" in message:
        # Do something
        pass
```

## Creating a TCL Script

1. Create a `.tcl` file in this directory
2. Define a `setup` procedure that will be called on load
3. Optionally define a `teardown` procedure for cleanup
4. Use `pyechat_log` and `pyechat_send` commands to interact with PyeChat

## Example TCL Script

```tcl
# Setup procedure - called when script loads
proc setup {} {
    pyechat_log "My TCL script loaded!"
}

# Teardown procedure - called when script unloads
proc teardown {} {
    pyechat_log "My TCL script unloaded!"
}

# Custom procedure
proc my_function {arg} {
    pyechat_log "Processing: $arg"
    # Send a message to IRC
    # pyechat_send "Rizon" "#channel" "Hello from TCL!"
}
```

## TCL API Reference

### Available Commands
- `pyechat_log <message>` - Print a log message to console
- `pyechat_send <network> <target> <message>` - Send IRC message

### Standard TCL
All standard TCL commands are available:
- String manipulation: `string`, `regexp`, `regsub`
- Lists: `list`, `lappend`, `lindex`, `foreach`
- Control flow: `if`, `for`, `while`, `switch`
- Procedures: `proc`, `return`
- Variables: `set`, `unset`, `incr`
- File I/O: `open`, `read`, `write`, `close`

## Available APIs (Python)

### Main Window
- `main_window.clients` - Dictionary of IRC clients (key: network name)
- `main_window.buffers` - Dictionary of message buffers (key: (network, target))
- `main_window.on_message(network, target, message, tags)` - Display a message
- `main_window.settings` - Application settings dictionary

### IRC Client Signals
Connect to these signals to handle events:
- `received_message(target, message, tags)` - Incoming message
- `connected_to_server(network_name)` - Connected
- `disconnected_from_server(network_name)` - Disconnected
- `received_nick_list(channel, nick)` - User joined channel
- `nick_changed(old_nick, new_nick)` - Nick change
- `received_kick(channel, target, kicker, reason)` - User kicked
- `received_mode(channel, sender, mode)` - Mode change
- `received_notice(target, sender, message)` - Notice received
- `received_invite(channel, sender, invited_nick)` - Invite received
- `received_action(target, sender, message)` - Action (/me) message

### IRC Client Methods
- `client.send_command(command)` - Send raw IRC command
- `client.nickname` - Current nickname
- `client.server` - Server address

## Tips

- Scripts are loaded in alphabetical order
- Use `_` prefix (e.g., `_disabled.py` or `_disabled.tcl`) to prevent loading
- Check `example_script.py` and `example_script.tcl` for working examples
- Python scripts run in the main GUI thread - avoid blocking operations
- TCL scripts share a single interpreter instance across all TCL scripts
- TCL scripts have access to standard TCL commands and file I/O
