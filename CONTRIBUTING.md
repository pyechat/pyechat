# Contributing to PyeChat

Thank you for your interest in contributing to PyeChat! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful and constructive. We're all here to make a great IRC client.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in GitHub Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - PyQt5 version and OS info

### Suggesting Features

1. Open an issue describing the feature
2. Explain the use case
3. Discuss the implementation approach

### Submitting Code

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Follow the code style**
   - Use PEP 8 for Python code
   - Keep lines under 100 characters
   - Add docstrings to functions
   - Use meaningful variable names

4. **Test your changes**
   - Ensure the app launches
   - Test affected functionality
   - Check for console errors

5. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: description"
   ```

6. **Push and create Pull Request**
   ```bash
   git push origin feature/amazing-feature
   ```

## Project Structure

```
pyechat/
├── assets/          # Icons and desktop files
├── data/            # User configuration files
├── src/
│   ├── gui/         # GUI components
│   │   ├── dialogs/ # Dialog windows
│   │   ├── utils/   # GUI utilities
│   │   └── main_window.py
│   └── irc/         # IRC protocol
└── main.py          # Entry point
```

## Code Style

### Python

- Follow PEP 8
- Use type hints where helpful
- Document public APIs
- Keep functions focused and small

### Naming

- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_CASE` for constants

### Example

```python
# Good
def calculate_message_hash(message: str) -> str:
    \"\"\"Calculate hash of IRC message.
    
    Args:
        message: The IRC message to hash
        
    Returns:
        Hexadecimal hash string
    \"\"\"
    return hashlib.md5(message.encode()).hexdigest()

# Bad
def calc(m):
    return hashlib.md5(m.encode()).hexdigest()
```

## Areas for Contribution

- **Bug fixes** - Always welcome!
- **IRC protocol** - CTCP, DCC, additional commands
- **GUI features** - New dialogs, widgets, themes
- **Performance** - Optimization, profiling
- **Documentation** - Improve README, add examples
- **Tests** - Unit tests, integration tests

## Questions?

Feel free to open an issue or discussion to ask questions!
