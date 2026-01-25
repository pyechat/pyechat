# PyeChat - A Modern PyQt5 IRC Client

PyeChat is a feature-rich, modern IRC client built with PyQt5, inspired by [HexChat](https://hexchat.github.io/). With support for multi-network connections, extensive theming, and a powerful plugin system, PyeChat delivers a comfortable and customizable IRC experience.

## Official Channels
Join our official channels to get support, share ideas, or connect with the community:
- **Rizon**: `ircs://irc.rizon.net/#pyechat`
- **Libera.Chat**: `ircs://irc.libera.chat/#pyechat`

## Features

### Core IRC Features
- **Multi-network support** — Connect to multiple IRC networks simultaneously
- **SSL/TLS support** — Secure connections with SSL/TLS encryption (OpenSSL 3.x compatible)
- **SASL authentication** — PLAIN and EXTERNAL methods supported
- **IRCv3 capabilities** — server-time, multi-prefix, away-notify, account-notify, extended-join
- **Auto-reconnect** — Automatic reconnection with configurable retry
- **Auto-commands** — Execute commands automatically on connect (e.g., NickServ identification)
- **CTCP support** — Responds to VERSION, PING, TIME requests

### User Interface
- **7 built-in themes** — Dark (Default), Dracula, Monokai, Solarized Dark, Nord, Gruvbox Dark, and Light
- **Nick coloring** — Deterministic nick colors based on username
- **Activity tracking** — Highlights channels with new messages or mentions
- **Message batching** — Optimized rendering for high-traffic channels (100ms batching, 500 msg/batch)
- **Real-time nick list** — Shows users with proper rank symbols (@, +, etc.)
- **Enhanced WHOIS** — Colorized, formatted WHOIS responses
- **Context menus** — Right-click menus for channels and users
- **Highlight mentions** — Visual highlighting when your nick is mentioned
- **Customizable appearance** — Full color control for every UI element

### Message Formatting
- **Bold**, *italic*, <u>underline</u> text support
- **mIRC color codes** — Full 16-color palette
- **URL detection** — Auto-linkifies HTTP(S) URLs (clickable links)
- **IRC formatting to HTML** — Converts IRC codes to rich HTML display
- **Custom event formatting** — Customize JOIN, PART, KICK, MODE messages with colors

### Advanced Features
- **Plugin system** — Auto-loading for both Python (.py) and TCL (.tcl) scripts
- **Shell command execution** — `/exec` command for running shell commands (with `-o` flag for channel output)
- **Tab completion** — Intelligent nick and channel name completion with cycling
- **Chat logging** — Automatic logging to disk (per-network, per-channel)
- **Smart input box** — Auto-expanding input (30-85px) with Shift+Enter for newlines
- **Connection info levels** — Minimal, Standard, or Verbose server message filtering
- **Channel events** — Tracks JOIN, PART, QUIT, KICK, MODE, NICK changes
- **NOTICE and ACTION support** — Proper handling of NOTICE messages and /me actions
- **Persistent settings** — All preferences saved to JSON configuration

## Recent Notable Additions (2026-01-25)
The project has received several UI and functionality improvements to make PyeChat feel more polished and powerful. Key highlights:

- **Colored Nicknames & Nicklist** — Deterministic nick coloring in chat and in the nick list (right side) for easier scanning of users.
- **Channel Management Dialog** — New dialog to view and edit channel metadata: topic editor, mode editor, and a ban list viewer/editor. The dialog requests the ban list on open and supports adding/removing bans.
- **Banlist Parsing (RFC numerics)** — Proper handling of RPL_BANLIST (367) and RPL_ENDOFBANLIST (368) so ban entries populate the Channel Management ban table.
- **Smart Join/Part Filtering** — Settings to hide join/part/quit messages or enable smart filtering that suppresses noise for users who haven't been active recently (configurable window).
- **MODE Handling Fixes** — Mode changes no longer duplicate in the chat; mode processing updates nick prefixes and updates the nick list without double-posting.
- **Improved Context Menus** — Right-click in chat now detects nick clicks reliably and shows per-nick operations (whois, kick/ban, voice/op), while channel right-click offers Channel Management and Sysinfo.
- **/SYSINFO Command** — New `/SYSINFO` command and UI action to broadcast concise system info (uptime, memory, OS) to a channel or send it privately.
- **Command Aliases** — Added short aliases for convenience (e.g. `/j` → `/join`, `/ns` → `/msg NickServ`, and other service shortcuts).
- **Input History** — Up/Down arrow history navigation in the message input for quick recall and editing of previous messages.
- **Startup & Plugin Loader Reliability** — Fixed startup scheduling so the Network List reliably opens on first run and plugin loader messages are restored to stdout/UI logs; added delayed theme re-apply to prevent flash.
- **Event & Numeric Improvements** — Better handling of topic metadata (RPL_TOPICWHOTIME / 333), channel modes (324), and more robust formatting for server numerics so replies appear in the correct buffer.

> Note: These changes were implemented incrementally; see the Git history for granular commits and more context.

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
│   ├── example_script.py  # Example Python plugin implementation
│   ├── example_script.tcl # Example TCL plugin implementation
│   └── README.md          # Plugin API documentation
├── src/                 # Source code
│   ├── gui/             # GUI components
│   │   ├── dialogs/     # Dialog windows
│   │   │   ├── network_edit.py   # Network configuration dialog
│   │   │   ├── network_list.py   # Network list dialog
│   │   │   └── settings.py       # Settings dialog with 4 tabs
│   │   ├── utils/       # GUI utilities
│   │   │   ├── colors.py         # Nick color generation
│   │   │   ├── formatters.py     # IRC to HTML conversion
│   │   │   ├── themes.py         # Theme presets (7 built-in themes)
│   │   │   └── whois.py          # WHOIS response formatting
│   │   └── main_window.py        # Main application window (1000+ lines)
│   ├── irc/             # IRC protocol implementation
│   │   ├── irc_client.py         # IRC client with full protocol support
│   │   ├── logger.py             # Logging system
│   │   └── whois.py              # WHOIS numeric code handling
│   └── plugins/         # Plugin loader
│       └── loader.py             # Auto-loads .py and .tcl scripts
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

**Important: SSL/TLS Support**

For SSL/TLS connections to work properly on systems with OpenSSL 3.x, you **must** use the system PyQt5 package:

**Recommended (Ubuntu/Debian):**
```bash
sudo apt install python3-pyqt5
python3 main.py  # Run directly with system Python
```

**Optional - For TCL Script Support:**
```bash
sudo apt install python3-tk  # Enables .tcl scripts in scripts/ directory
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
- `/exec [-o] <command>` - Execute shell command (use `-o` to send output to current channel)

### Theme System

PyeChat includes 7 professionally designed themes with optimized contrast and readability:

#### Dark (Default)
Classic dark theme with charcoal backgrounds and high-contrast text. Features Ubuntu Orange highlights.
- Background: `#1e1e1e` (Charcoal)
- Foreground: `#e0e0e0` (Light Gray)
- Highlight: `#E95420` (Ubuntu Orange)

#### Dracula
Popular vampire-themed palette with purple tones and vibrant accents.
- Background: `#282a36` (Dark Purple)
- Foreground: `#f8f8f2` (Off-White)
- Highlight: `#ff79c6` (Pink)

#### Monokai
Warm dark theme inspired by Sublime Text's default color scheme.
- Background: `#272822` (Dark Brown)
- Foreground: `#f8f8f2` (Off-White)
- Highlight: `#f92672` (Hot Pink)

#### Solarized Dark
Precision-designed dark theme with reduced brightness contrast for eye comfort.
- Background: `#002b36` (Deep Blue)
- Foreground: `#839496` (Gray-Blue)
- Highlight: `#268bd2` (Blue)

#### Nord
Arctic, north-bluish color palette with calm, smooth colors.
- Background: `#2e3440` (Dark Slate)
- Foreground: `#d8dee9` (Snow White)
- Highlight: `#88c0d0` (Frost Blue)

#### Gruvbox Dark
Retro groove theme with warm, earthy tones.
- Background: `#282828` (Dark Brown)
- Foreground: `#ebdbb2` (Cream)
- Highlight: `#fb4934` (Red)

#### Light
Clean light theme for well-lit environments, GitHub-inspired.
- Background: `#ffffff` (White)
- Foreground: `#24292e` (Dark Gray)
- Highlight: `#0366d6` (Blue)

**Switching Themes:**
1. Open Settings (PyeChat → Settings)
2. Go to Appearance tab
3. Select a preset from the dropdown
4. Click "Apply Preset"
5. Changes take effect immediately

You can also fully customize any theme by adjusting individual color settings.

### Plugin System

PyeChat features a powerful plugin system that auto-loads scripts from the `scripts/` directory on startup. Both Python and TCL scripts are supported!

#### Python Plugins

Python plugins can hook into IRC events, access the main window, and extend functionality.

**Creating a Python plugin:**
1. Create a `.py` file in the `scripts/` directory
2. Implement a `setup(main_window)` function
3. Connect to signals or add custom functionality
4. Optional: Implement `teardown()` for cleanup

**Example Python plugin:**
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

#### TCL Plugins

TCL plugins provide a familiar scripting environment similar to other IRC clients like Eggdrop.

**Creating a TCL plugin:**
1. Install TCL support: `sudo apt install python3-tk`
2. Create a `.tcl` file in the `scripts/` directory
3. Use built-in commands: `pyechat_log`, `pyechat_send`

**Example TCL plugin:**
```tcl
# Example TCL script for PyeChat
proc greet {nick} {
    pyechat_log "Hello from TCL, $nick!"
}

# Call the procedure
greet "world"

# You can also send IRC commands
# pyechat_send "network_name" "/msg #channel Hello from TCL!"
```

**Available TCL Commands:**
- `pyechat_log <message>` - Log a message to stdout
- `pyechat_send <network> <command>` - Send IRC command to network

**Plugin Features:**
- Auto-loading on startup
- Access to all IRC events
- Full access to main window and IRC clients (Python)
- Signal/slot connections (Python)
- Custom IRC commands
- State persistence across restarts

See `scripts/README.md` and example scripts for full API documentation.

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
- **Theme presets** - 7 built-in themes (Dark, Dracula, Monokai, Solarized Dark, Nord, Gruvbox Dark, Light)
- **Custom colors** - Full control over every UI element:
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

## Shell Command Execution

The `/exec` command allows you to run shell commands directly from IRC:

**Basic usage:**
```
/exec ls -la
```
Output is displayed in the current window.

**Send output to channel:**
```
/exec -o uptime
```
The `-o` flag sends command output to the current channel (useful for showing system info).

**Features:**
- 10-second timeout to prevent hanging
- STDOUT and STDERR are both captured
- Works in channels and private messages
- Exit code displayed on completion

**Example use cases:**
- `/exec -o uname -a` - Show system information in channel
- `/exec date` - Check current date/time
- `/exec df -h` - Check disk space
- `/exec -o fortune` - Share a random quote

**Security note:** Commands run with your user permissions. Be careful when using `-o` in public channels.

## Development

### Code Organization
- `src/gui/main_window.py` - Main application window with message batching, theme system, and UI management
- `src/gui/dialogs/` - Modular dialog components (network list, network edit, settings with theme selector)
- `src/gui/utils/` - Shared GUI utilities (colors, formatters, WHOIS, theme presets)
- `src/irc/irc_client.py` - Full IRC protocol implementation with IRCv3 and SSL/TLS support
- `src/irc/whois.py` - WHOIS numeric code handling
- `src/irc/logger.py` - Per-network/channel logging system
- `src/plugins/loader.py` - Auto-loads Python (.py) and TCL (.tcl) scripts on startup

### Architecture
- **Signal-based communication** - PyQt signals for IRC events
- **Message batching** - 100ms timer, max 500 messages per batch for performance
- **Nick list optimization** - Debounced updates (100ms delay)
- **Buffer management** - Separate buffers for each network/channel (2500 message limit)
- **Event system** - Generic event handlers for extensibility

### Contributing

Contributions are welcome! This is a fork of [ComputerTech312/pyechat](https://github.com/ComputerTech312/pyechat).

**To contribute:**
1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development Workflow (for maintainers):**
```bash
# Sync with upstream
git fetch upstream
git merge upstream/main
git push origin main

# Make changes and push
git add -A
git commit -m "Description of changes"
git push origin main
```

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

## Known Issues & Limitations

- No DCC file transfer support (yet)
- Self-signed SSL certificates are auto-accepted (not validated)
- **OpenSSL Compatibility**: For best SSL/TLS support on systems with OpenSSL 3.x, use system PyQt5 packages (`sudo apt install python3-pyqt5`) instead of pip
- TCL plugins require python3-tk package for full functionality

## Future Enhancements

- DCC file transfer support
- Spell checking
- Channel logging viewer/search
- Custom keyboard shortcuts
- Plugin marketplace/browser
- More theme presets
- Notification system improvements

## License

MIT License - See [LICENSE](LICENSE) file for details

Copyright (c) 2026 Colby (ComputerTech312)

## Credits

- Inspired by [HexChat](https://hexchat.github.io/)
- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)

## Links

- **Repository**: https://github.com/lord3nd3r/pyechat
- **Official IRC**: #pyechat on irc.rizon.net and irc.libera.chat
