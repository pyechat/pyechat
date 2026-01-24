# PyeChat - A Modern PyQt5 IRC Client

PyeChat is a modern, user-friendly IRC client built with PyQt5. It's inspired by the design and functionality of [HexChat](https://hexchat.github.io/).

## Official Channels
Join our official channels to get support, share ideas, or connect with the community:
- **Rizon**: `ircs://irc.rizon.net/#pyechat`
- **Libera.Chat**: `ircs://irc.libera.chat/#pyechat`

## Features

### Core IRC Features
- 🌐 **Multi-network support** - Connect to multiple IRC networks simultaneously
- 🔒 **SSL/TLS support** - Secure connections with SSL/TLS encryption
- 🔑 **SASL authentication** - PLAIN and EXTERNAL methods supported
- 🚀 **IRCv3 capabilities** - server-time, multi-prefix, away-notify, account-notify, extended-join
- 🤖 **Auto-reconnect** - Automatic reconnection with configurable retry
- 📝 **Auto-commands** - Execute commands automatically on connect (e.g., NickServ identification)
- 🔔 **CTCP support** - Responds to VERSION, PING, TIME requests

### User Interface
- 🎨 **Customizable themes** - Full color customization with light/dark mode support
- 🌈 **Nick coloring** - Deterministic nick colors based on username
- ⭐ **Activity tracking** - Highlights channels with new messages or mentions
- 💬 **Message batching** - Optimized rendering for performance
- 📊 **Real-time nick list** - Shows users with proper rank symbols (@, +, etc.)
- 🔍 **WHOIS formatting** - Enhanced, colorized WHOIS responses
- 📋 **Context menus** - Right-click menus for channels and users
- 🎯 **Highlight mentions** - Visual highlighting when your nick is mentioned

### Message Formatting
- **Bold**, *italic*, <u>underline</u> text support
- 🎨 **mIRC color codes** - Full 16-color palette
- 🔗 **URL detection** - Auto-linkifies HTTP(S) URLs
- 💬 **IRC formatting to HTML** - Converts IRC codes to rich HTML display
- ✨ **Custom event formatting** - Customize JOIN, PART, KICK, MODE messages with colors

### Advanced Features
- ⌨️ **Tab completion** - Intelligent nick and channel name completion with cycling
- 📝 **Chat logging** - Automatic logging to disk (per-network, per-channel)
- 🔄 **Smart input box** - Auto-expanding input (30-85px) with Shift+Enter for newlines
- ⚙️ **Connection info levels** - Minimal, Standard, or Verbose server message filtering
- 🎭 **Channel events** - Tracks JOIN, PART, QUIT, KICK, MODE, NICK changes
- 📢 **NOTICE and ACTION support** - Proper handling of NOTICE messages and /me actions
- 💾 **Persistent settings** - All preferences saved to JSON configuration
- 🔌 **Plugin system** - Auto-loading Python scripts from `scripts/` directory for extensibility

## Project Structure
```
pyechat/
├── assets/              # Icons and desktop files
│   ├── pyechat.png      # Application icon
│   ├── pyechat.ico      # Windows icon
│   └── pyechat.desktop  # Linux desktop entry
├── data/                # User configuration (auto-created)
│   ├── networks.json    # Network configurations
│   └── settings.json    # User preferences
├── logs/                # Chat logs (per network/channel)
├── scripts/             # User plugins (auto-loaded on startup)
│   ├── example_script.py # Example plugin implementation
│   └── README.md         # Plugin API documentation
├── src/                 # Source code
│   ├── gui/             # GUI components
│   │   ├── dialogs/     # Dialog windows
│   │   │   ├── network_edit.py   # Network configuration dialog
│   │   │   ├── network_list.py   # Network list dialog
│   │   │   └── settings.py       # Settings dialog with 4 tabs
│   │   ├── utils/       # GUI utilities
│   │   │   ├── colors.py         # Nick color generation
│   │   │   ├── formatters.py     # IRC to HTML conversion
│   │   │   └── whois.py          # WHOIS response formatting
│   │   └── main_window.py        # Main application window (1000+ lines)
│   ├── irc/             # IRC protocol implementation
│   │   ├── irc_client.py         # IRC client with full protocol support
│   │   ├── logger.py             # Logging system
│   │   └── whois.py              # WHOIS numeric code handling
│   └── plugins/         # Plugin loader
│       └── loader.py             # Dynamic script loading system
├── main.py              # Application entry point
├── setup.py             # Package configuration
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Getting Started

### Prerequisites
- Python 3.8 or higher (tested up to 3.13)
- PyQt5 5.15.0 or higher

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/lord3nd3r/pyechat.git
cd pyechat
```

2. **Install dependencies**

**⚠️ Important: SSL/TLS Support**

For SSL/TLS connections to work properly on systems with OpenSSL 3.x, you **must** use the system PyQt5 package:

**Recommended (Ubuntu/Debian):**
```bash
sudo apt install python3-pyqt5
python3 main.py  # Run directly with system Python
```

**Alternative with pip** (may have SSL issues on OpenSSL 3.x):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install PyQt5
python main.py
```

**Note:** The pip version of PyQt5 may have OpenSSL compatibility issues. If you see `Incompatible version of OpenSSL` errors, use the system package method above.

3. **Run PyeChat**
```bash
python3 main.py  # If using system packages
# OR
python main.py   # If using venv
```

### Quick Start

On first launch:
1. The Network List dialog will appear
2. Click "Add" to create a new network configuration
3. Fill in server details (host, port, nickname)
4. Add auto-join channels (comma-separated)
5. Configure SSL/SASL if needed
6. Click "Connect"

### IRC Commands

PyeChat supports standard IRC commands:
- `/join #channel` - Join a channel
- `/part [#channel]` - Leave a channel (current if not specified)
- `/msg <nick> <message>` - Send private message
- `/query <nick>` - Open PM window
- `/me <action>` - Send action message
- `/nick <newnick>` - Change nickname
- `/whois <nick>` - Get user information
- `/quit [message]` - Disconnect with optional quit message
- `/raw <command>` or `/quote <command>` - Send raw IRC command

### Plugin System

PyeChat supports Python plugins that auto-load from the `scripts/` directory on startup. Plugins can:
- Hook into IRC events (messages, joins, parts, etc.)
- Access the main window and all IRC clients
- Add custom functionality without modifying core code

**Creating a plugin:**
1. Create a `.py` file in the `scripts/` directory
2. Implement a `setup(main_window)` function
3. Connect to signals or add custom functionality
4. Optional: Implement `teardown()` for cleanup

**Example:**
```python
def setup(main_window):
    """Called when plugin loads"""
    def on_message(network, target, sender, message):
        if "hello" in message.lower():
            print(f"[{network}] {sender} said hello in {target}!")
    
    for client in main_window.clients.values():
        client.message_received.connect(on_message)
    
    print("My plugin loaded!")

def teardown():
    """Optional cleanup when plugin unloads"""
    print("My plugin unloaded!")
```

See `scripts/README.md` for full API documentation.

## Configuration

### Networks
Network configurations are stored in `data/networks.json`. Each network can have:
- **Name** - Display name for the network
- **Host & Port** - IRC server address
- **SSL** - Enable SSL/TLS encryption
- **SASL** - Authentication method (None, PLAIN, EXTERNAL)
- **Nickname & Real Name** - Your identity
- **Server Password** - Optional server password
- **Auto-join Channels** - Channels to join on connect
- **Auto-commands** - Commands to run after connecting (e.g., NickServ identification)

Edit networks through: **PyeChat → Network List**

### Settings
User preferences are stored in `data/settings.json`. The settings dialog has 4 tabs:

#### General Tab
- Show/hide timestamps with custom format
- Toggle JOIN/PART/QUIT events
- Auto-reconnect on disconnect
- Nick coloring
- Highlight mentions
- Connection info level (Minimal/Standard/Verbose)
- Tab completion suffix

#### Events Tab
- Customize format for IRC events (JOIN, PART, KICK, MODE, etc.)
- Set custom colors for each event type
- Use placeholders like `{nick}`, `{channel}`, `{reason}`

#### Appearance Tab
- **System Default** or **Custom** theme
- Full color customization:
  - Chat area (background, text, timestamps)
  - Tree/channel list (background, text, selection)
  - Nick list (background, text, selection)
  - Topic bar, input box, menus, status bar
  - Borders, scrollbars, highlight colors
- Font selection
- Live preview of theme changes

#### Identity Tab
- Default nickname
- Real name (GECOS)

Access settings via: **PyeChat → Settings**

### Dark Theme
PyeChat includes a comfortable dark theme optimized to reduce eye strain. The theme uses:
- Dark charcoal backgrounds (#1e1e1e)
- High-contrast light text (#e0e0e0)
- Ubuntu Orange (#E95420) for selections and highlights
- Subtle borders and properly styled scrollbars

## Development

### Code Organization
- `src/gui/main_window.py` - Main application window with message batching and UI management
- `src/gui/dialogs/` - Modular dialog components (network list, network edit, settings)
- `src/gui/utils/` - Shared GUI utilities (colors, formatters, WHOIS)
- `src/irc/irc_client.py` - Full IRC protocol implementation with IRCv3 support
- `src/irc/whois.py` - WHOIS numeric code handling
- `src/irc/logger.py` - Logging system

### Architecture
- **Signal-based communication** - PyQt signals for IRC events
- **Message batching** - 100ms timer, max 500 messages per batch for performance
- **Nick list optimization** - Debounced updates (100ms delay)
- **Buffer management** - Separate buffers for each network/channel (2500 message limit)
- **Event system** - Generic event handlers for extensibility

### Contributing

Contributions are welcome!

To contribute:
1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Performance Notes

- **Message batching** prevents UI freezing during high-traffic channels
- **Nick list updates** are debounced to reduce redraws
- **Buffer size limits** (2500 messages) prevent memory bloat
- **Lazy tree item creation** improves startup time
- **HTML caching** in buffers reduces rendering overhead

## Platform Support

- ✅ **Linux** - Primary platform (tested on Ubuntu)
- ✅ **Windows** - Should work (PyQt5 is cross-platform)
- ⚠️ **macOS** - Untested but should work

## Known Issues

- No DCC file transfer support (yet)
- Self-signed SSL certificates are auto-accepted
- **OpenSSL Compatibility**: For best SSL/TLS support on systems with OpenSSL 3.x, use system PyQt5 packages (`sudo apt install python3-pyqt5`)

## License

MIT License - See [LICENSE](LICENSE) file for details

Copyright (c) 2026 Colby (ComputerTech312)

## Credits

- Inspired by [HexChat](https://hexchat.github.io/)
- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)

## Links

- **Repository**: https://github.com/lord3nd3r/pyechat
- **Official IRC**: #pyechat on irc.rizon.net and irc.libera.chat
