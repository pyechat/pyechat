# PyeChat Scripts

This directory contains Python scripts that are automatically loaded when PyeChat starts.

## Creating a Script

1. Create a `.py` file in this directory
2. Define a `setup(main_window)` function that will be called on load
3. Optionally define a `teardown(main_window)` function for cleanup

## Example Script

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

## Available APIs

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
- Use `_` prefix (e.g., `_disabled.py`) to prevent loading
- Check `example_script.py` for a working example
- Scripts run in the main GUI thread - avoid blocking operations
