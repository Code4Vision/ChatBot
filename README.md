# CLI Local AI Chatbot

A secure command-line chatbot with local authentication, encrypted storage, and AI capabilities.

## Overview

This Python-based CLI chatbot provides:
- Secure local user authentication
- Encrypted chat history storage
- Local AI processing capabilities
- Cross-platform compatibility
- Offline functionality

## Features

- 🔒 **Secure Authentication**: Local username/password authentication with secure password hashing
- 🔐 **Data Encryption**: All chat history and user preferences encrypted at rest
- 🤖 **Local AI**: GPT4All integration for offline AI responses
- 💾 **Database Storage**: SQLAlchemy-based storage with SQLite
- 🔑 **Session Management**: Secure session handling and user preferences
- 📱 **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Start
1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables:
   ```bash
   # Generate encryption key (keep this secure!)
   export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   ```
4. Run the application:
   ```bash
   python cli_chatbot.py
   ```

## Converting to Executable File

### Method 1: PyInstaller (Recommended)

#### Installation
```bash
pip install pyinstaller
```

#### Create Single Executable

**For Windows (.exe):**
```bash
pyinstaller --onefile --console --name "ChatbotAI" cli_chatbot.py
```

**For macOS/Linux:**
```bash
pyinstaller --onefile --console --name "chatbot-ai" cli_chatbot.py
```

#### Advanced Build Options
```bash
# With icon (Windows)
pyinstaller --onefile --console --icon=icon.ico --name "ChatbotAI" cli_chatbot.py

# Hidden console (Windows GUI-style)
pyinstaller --onefile --noconsole --name "ChatbotAI" cli_chatbot.py

# Include all dependencies explicitly
pyinstaller --onefile --console --hidden-import=sqlalchemy --hidden-import=cryptography --name "ChatbotAI" cli_chatbot.py
```

#### Distribution
The executable will be created in the `dist/` folder. Distribute along with:
- A `.env` file or setup script for the encryption key
- Installation instructions for end users

### Method 2: cx_Freeze (Alternative)

```bash
pip install cx-freeze
```

Create `setup.py`:
```python
from cx_Freeze import setup, Executable

setup(
    name="ChatbotAI",
    version="1.0",
    description="Local AI Chatbot",
    executables=[Executable("cli_chatbot.py")]
)
```

Build:
```bash
python setup.py build
```

### Method 3: Auto-py-to-exe (GUI Tool)

```bash
pip install auto-py-to-exe
auto-py-to-exe
```

Use the GUI interface to configure and build your executable.

## Cross-Platform Deployment

### Windows
- **Executable**: `.exe` files
- **Installer**: Use tools like NSIS or Inno Setup
- **Dependencies**: Include Visual C++ Redistributable if needed

### macOS
- **Application Bundle**: Create `.app` bundles
- **DMG Distribution**: Package in disk image files
- **Code Signing**: Sign for security (requires Apple Developer account)

### Linux
- **AppImage**: Portable application format
- **Snap Packages**: Universal Linux packages
- **Flatpak**: Sandboxed application distribution

## Making It Operational Across Devices

### 1. Environment Setup

Create a setup script (`setup.sh` for Unix/Linux/macOS, `setup.bat` for Windows):

**setup.sh:**
```bash
#!/bin/bash
echo "Setting up ChatbotAI..."
if [ -z "$ENCRYPTION_KEY" ]; then
    export ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "Generated encryption key. Save this securely: $ENCRYPTION_KEY"
    echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" > .env
fi
chmod +x chatbot-ai
echo "Setup complete! Run ./chatbot-ai to start"
```

**setup.bat:**
```batch
@echo off
echo Setting up ChatbotAI...
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())" > .env
echo Setup complete! Run ChatbotAI.exe to start
pause
```

### 2. Responsive Design Considerations

While this is a CLI application, for future web interface development:

#### Frontend Technologies
- **Bootstrap 5**: Mobile-first responsive framework
- **CSS Grid/Flexbox**: Modern layout techniques
- **Progressive Web App (PWA)**: Offline capabilities

#### Responsive Breakpoints
```css
/* Mobile First */
@media (min-width: 576px) { /* Small devices */ }
@media (min-width: 768px) { /* Medium devices */ }
@media (min-width: 992px) { /* Large devices */ }
@media (min-width: 1200px) { /* Extra large devices */ }
```

### 3. CLI Responsive Features

The current CLI application includes:
- **Terminal Width Adaptation**: Text wrapping for different terminal sizes
- **Cross-Platform Commands**: Works on various terminal emulators
- **Keyboard Navigation**: Standard input handling across platforms

## Configuration

### Environment Variables
- `ENCRYPTION_KEY`: Required for data encryption (generate with Fernet)
- `DATABASE_URL`: Optional database connection (defaults to SQLite)

### User Preferences
The application stores encrypted user preferences including:
- Display settings
- AI model preferences
- Chat history retention settings

## Security Features

- **Password Hashing**: Werkzeug's secure password hashing
- **Data Encryption**: Fernet encryption for all stored data
- **Session Security**: Secure session management
- **Input Validation**: Protection against common attacks

## Development

### Running in Development Mode
```bash
python cli_chatbot.py
```

### Testing
```bash
# Run basic functionality test
python -c "import cli_chatbot; print('Import successful')"
```

### Building for Distribution
```bash
# Create requirements file
pip freeze > requirements.txt

# Build executable
pyinstaller --onefile cli_chatbot.py

# Test executable
./dist/cli_chatbot
```

## Troubleshooting

### Common Issues

**Missing Dependencies:**
```bash
pip install --upgrade cryptography sqlalchemy werkzeug
```

**Encryption Key Error:**
```bash
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

**Database Connection Issues:**
- Check file permissions for `chatbot.db`
- Ensure SQLite is available on the system

**Executable Issues:**
- Include all hidden imports in PyInstaller
- Test on the target platform before distribution
- Check antivirus software (may flag unknown executables)

## License

[Specify your license here]

## Contributing

[Add contribution guidelines if applicable]

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review error messages carefully
3. Ensure all dependencies are installed
4. Verify environment variables are set correctly

---

**Note**: Always keep your encryption key secure and backed up. Loss of the encryption key means loss of all encrypted data.