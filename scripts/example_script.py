"""
Example PyeChat Script

This demonstrates how to create scripts for PyeChat.

Scripts should define a setup(main_window) function that will be called on load.
Optionally, define a teardown(main_window) function for cleanup.

Available APIs:
- main_window.clients - Dictionary of IRC clients by network name
- main_window.buffers - Dictionary of message buffers
- main_window.on_message(network, target, message, tags) - Display a message
- IRC client signals: received_message, connected_to_server, etc.
"""


def setup(main_window):
    """Called when the script is loaded."""
    print("Example script loaded!")
    
    # Example: Connect to IRC events
    for network_name, client in main_window.clients.items():
        # Listen for messages
        client.received_message.connect(
            lambda target, msg, tags, nw=network_name: on_message(main_window, nw, target, msg)
        )


def teardown(main_window):
    """Called when the script is unloaded."""
    print("Example script unloaded!")


def on_message(main_window, network, target, message):
    """Handle incoming IRC messages."""
    # Example: Auto-respond to specific messages
    if "!hello" in message.lower():
        # Get the IRC client for this network
        client = main_window.clients.get(network)
        if client and target.startswith('#'):
            # Send a response
            client.send_command(f"PRIVMSG {target} :Hello from PyeChat script!")
