# PyeChat - A Modern PyQt5 IRC Client

PyeChat is a modern, user-friendly IRC client built with PyQt5. It's inspired by the design and functionality of [HexChat](https://hexchat.github.io/).

## Official Channels
Join our official channels to get support, share ideas, or connect with the community:
- **Rizon**: `ircs://irc.rizon.net/#pyechat`
- **Libera.Chat**: `ircs://irc.libera.chat/#pyechat`

## Features
- 🎨 Modern, customizable UI with theme support
- 🌐 Support for multiple IRC networks
- 🔒 SSL/TLS and SASL authentication
- 💬 Nick color coding and tab completion
- 📝 Message formatting (bold, italic, colors)
- ⚙️ Persistent settings and network configurations
- 🎯 Highlight mentions and custom event formatting

## Project Structure
```
pyechat/
├── assets/          # Icons and desktop files
│   ├── pyechat.ico
│   └── pyechat.desktop
├── data/            # User configuration (auto-created)
│   ├── networks.json
│   └── settings.json
├── logs/            # Application logs
├── src/             # Source code
│   ├── gui/         # GUI components
│   │   ├── dialogs/ # Dialog windows
│   │   ├── utils/   # GUI utilities
│   │   └── main_window.py
│   └── irc/         # IRC protocol implementation
├── main.py          # Application entry point
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.8+
- PyQt5

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/pyechat.git
cd pyechat
```

2. **Install dependencies**

Using pip:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install PyQt5
```

Or using system packages (Ubuntu/Debian):
```bash
sudo apt install python3-pyqt5
```

3. **Run PyeChat**
```bash
python main.py
```

## Configuration

### Networks
Network configurations are stored in `data/networks.json`. You can:
- Add/edit networks through the GUI (Server → Network List)
- Manually edit `data/networks.json`
- See `data/networks.example.json` for the format

### Settings
User preferences are stored in `data/settings.json`. You can customize:
- Appearance (colors, fonts)
- Behavior (timestamps, auto-reconnect)
- Event formatting
- Identity (default nickname, real name)

Access settings via: **Edit → Settings**

## Development

### Code Organization
- `src/gui/main_window.py` - Main application window
- `src/gui/dialogs/` - Modular dialog components
- `src/gui/utils/` - Shared GUI utilities
- `src/irc/` - IRC protocol implementation

### Running Tests
```bash
python -m pytest tests/
```

## License
[Add your license information here]

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## Credits
Inspired by [HexChat](https://hexchat.github.io/)
