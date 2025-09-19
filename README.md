# 🤖 Advanced CLI AI Chatbot

A comprehensive command-line AI chatbot with advanced capabilities including secure authentication, encrypted storage, mathematical calculations, group discussions, negotiation assistance, and intelligent suggestions.

## 🌟 Overview

This Python-based CLI chatbot is a complete conversational AI system that provides:
- **🔒 Secure Authentication**: Local username/password with encrypted storage
- **🧮 Mathematical Engine**: Advanced calculations with trigonometry, logarithms, and more
- **🤝 Convocation Tools**: Facilitate group discussions and gather diverse perspectives
- **⚖️ Negotiation Assistant**: Help resolve conflicts and reach agreements
- **💡 Smart Suggestions**: Intelligent recommendations and advice system
- **🤖 Local AI Processing**: GPT4All integration for offline responses
- **📱 Cross-Platform**: Works on Windows, macOS, and Linux

## ✨ Key Features

### 🔐 **Security & Privacy**
- **Local Authentication**: Username/password with secure Werkzeug hashing
- **Data Encryption**: All chat history encrypted using Fernet encryption
- **Session Management**: Secure session handling and user preferences
- **Input Validation**: Protection against code injection and security threats

### 🧮 **Mathematical Calculator**
- **Smart Detection**: Automatically recognizes math expressions in conversations
- **Advanced Functions**: Trigonometry (`sin`, `cos`, `tan`), logarithms (`log`, `log10`)
- **Mathematical Constants**: Support for `pi`, `e`, and other constants
- **Secure Evaluation**: AST-based parsing prevents code injection attacks
- **Calculator Mode**: Dedicated interactive calculator session

**Examples:**
```
Basic: 15 + 27, 100 / 4, 2^8
Advanced: sqrt(144), sin(pi/2), log10(1000)
Complex: (2^3 + 4) * sqrt(9), factorial(5)
```

### 🤝 **Convocation (Group Discussion)**
- **Multi-Perspective Analysis**: Gather different viewpoints on topics
- **Structured Discussions**: Organize thoughts and facilitate group conversations
- **Decision Making**: Help groups reach consensus and make informed decisions
- **Perspective Documentation**: Keep track of different viewpoints and arguments

### ⚖️ **Negotiation & Conflict Resolution**
- **Mediation Assistance**: Help resolve disputes and conflicts
- **Common Ground**: Identify shared interests and mutual benefits
- **Solution Generation**: Suggest compromises and win-win scenarios
- **Agreement Templates**: Structure negotiations for successful outcomes

### 💡 **Intelligent Suggestions**
- **Context-Aware Advice**: Personalized recommendations based on conversation
- **Problem-Solving**: Creative solutions and alternative approaches
- **Decision Support**: Pros/cons analysis and decision matrices
- **Resource Recommendations**: Suggest tools, methods, and next steps

### 🤖 **AI Integration**
- **Local Processing**: GPT4All integration for offline AI responses
- **Fallback System**: Graceful degradation when AI services are unavailable
- **Memory System**: Conversation context preservation across sessions
- **Personalization**: User preference integration for response customization

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.8+** (Python 3.11+ recommended)
- **pip** package manager

### Quick Start

1. **Clone or download the project**
   ```bash
   git clone <your-repository-url>
   cd cli-chatbot
   ```

2. **Install dependencies** (using uv - recommended):
   ```bash
   # Install uv package manager
   pip install uv
   
   # Install dependencies
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install cryptography flask flask-login flask-sqlalchemy flask-wtf
   pip install google-genai gpt4all requests sqlalchemy werkzeug wtforms
   ```

3. **Set encryption key**:
   ```bash
   # Generate secure encryption key
   export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   ```

4. **Run the application**:
   ```bash
   python cli_chatbot.py
   ```

## 🎯 How to Use

### Main Menu Options
```
1. Start Chat              - Begin AI conversation with all features
2. View Chat History       - Review previous conversations
3. 🧮 Mathematical Calculator - Dedicated calculator mode
4. Facilitate Discussion   - Convocation for group discussions
5. Negotiate & Resolve     - Conflict resolution assistance
6. Get Smart Suggestions   - Intelligent recommendations
7. Manage Preferences      - User settings and customization
8. Logout                  - Switch users securely
9. Exit                    - Close application
```

### Mathematical Calculator Usage
- **In Chat**: Type expressions like `2+2`, `sqrt(16)`, `sin(pi/2)`
- **Calculator Mode**: Choose option #3 for focused calculations
- **Help**: Type `help` in calculator mode for examples
- **Supported**: Basic arithmetic, trigonometry, logarithms, factorials, constants

### Convocation Features
- **Topic Introduction**: Present discussion topics clearly
- **Perspective Gathering**: Collect different viewpoints
- **Synthesis**: Combine perspectives for comprehensive understanding
- **Decision Making**: Guide groups toward consensus

### Negotiation Tools
- **Issue Identification**: Clarify points of disagreement
- **Interest Analysis**: Understand underlying needs and concerns
- **Option Generation**: Create multiple solution alternatives
- **Agreement Framework**: Structure successful negotiations

## 📱 Converting to Executable

### Method 1: PyInstaller (Recommended)

```bash
# Install PyInstaller
pip install pyinstaller

# Create single executable
pyinstaller --onefile --console --name "ChatbotAI" cli_chatbot.py
```

**Platform-Specific Builds:**

**Windows:**
```bash
pyinstaller --onefile --console --icon=icon.ico --name "ChatbotAI" cli_chatbot.py
```

**macOS:**
```bash
pyinstaller --onefile --console --name "chatbot-ai" cli_chatbot.py
```

**Linux:**
```bash
pyinstaller --onefile --console --name "chatbot-ai" cli_chatbot.py
```

**Advanced Options:**
```bash
# Include all dependencies explicitly
pyinstaller --onefile --console \
    --hidden-import=sqlalchemy \
    --hidden-import=cryptography \
    --hidden-import=gpt4all \
    --name "ChatbotAI" cli_chatbot.py

# GUI-style (hidden console)
pyinstaller --onefile --noconsole --name "ChatbotAI" cli_chatbot.py
```

### Method 2: cx_Freeze

```bash
pip install cx-freeze
```

Create `setup.py`:
```python
from cx_Freeze import setup, Executable

setup(
    name="Advanced CLI Chatbot",
    version="2.0",
    description="AI Chatbot with Math, Discussion, and Negotiation Tools",
    executables=[Executable("cli_chatbot.py", base="Console")]
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

## 🌐 Cross-Platform Deployment

### Windows Distribution
- **Executable**: `.exe` files with all dependencies included
- **Installer**: Use NSIS or Inno Setup for professional installation
- **Dependencies**: Include Visual C++ Redistributable if needed

### macOS Distribution
- **App Bundle**: Create `.app` bundles for macOS applications
- **DMG**: Package in disk image files for easy distribution
- **Code Signing**: Sign applications for security (requires Apple Developer account)

### Linux Distribution
- **AppImage**: Single-file portable applications
- **Snap Packages**: Universal Linux package format
- **Flatpak**: Sandboxed application distribution
- **deb/rpm**: Traditional Linux package formats

## 🛠️ Development Setup

### Environment Setup

**setup.sh (Unix/Linux/macOS):**
```bash
#!/bin/bash
echo "Setting up Advanced CLI Chatbot..."
if [ -z "$ENCRYPTION_KEY" ]; then
    export ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" > .env
    echo "Generated encryption key and saved to .env"
fi
echo "Setup complete! Run 'python cli_chatbot.py' to start"
```

**setup.bat (Windows):**
```batch
@echo off
echo Setting up Advanced CLI Chatbot...
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())" > .env
echo Encryption key generated and saved to .env
echo Setup complete! Run 'python cli_chatbot.py' to start
pause
```

### Configuration

**Environment Variables:**
- `ENCRYPTION_KEY`: **Required** - Fernet encryption key for data security
- `DATABASE_URL`: *Optional* - Database connection (defaults to SQLite)
- `GEMINI_API_KEY`: *Optional* - Google Gemini API for enhanced AI responses

**User Preferences:**
The application stores encrypted preferences including:
- AI response style and length
- Calculator display format
- Discussion facilitation preferences
- Chat history retention settings

## 🔧 Advanced Configuration

### Database Setup
```python
# Default SQLite (no configuration needed)
DATABASE_URL = "sqlite:///chatbot.db"

# PostgreSQL example
DATABASE_URL = "postgresql://user:password@localhost/chatbot"

# MySQL example  
DATABASE_URL = "mysql://user:password@localhost/chatbot"
```

### AI Model Configuration
```python
# GPT4All model options (download required)
MODEL_OPTIONS = {
    "orca-mini-3b": "orca-mini-3b-gguf2.Q4_0.gguf",
    "llama-2-7b": "llama-2-7b-chat.ggmlv3.q4_0.bin",
    "gpt4all-falcon": "gpt4all-falcon-q4_0.gguf"
}
```

## 🔒 Security Features

### Data Protection
- **Password Hashing**: Werkzeug's secure PBKDF2 with salt
- **Data Encryption**: Fernet symmetric encryption for all stored data
- **Session Security**: Secure session management with timeout
- **Input Sanitization**: AST-based mathematical evaluation prevents code injection

### Mathematical Security
- **AST Parsing**: Secure expression evaluation without `eval()`
- **Input Validation**: Length and complexity limits prevent DoS attacks
- **Function Whitelisting**: Only approved mathematical functions allowed
- **Resource Limits**: Prevents infinite calculations and memory exhaustion

## 🧪 Testing & Validation

### Basic Tests
```bash
# Test import and basic functionality
python -c "import cli_chatbot; print('✅ Import successful')"

# Test mathematical calculator
python -c "
from cli_chatbot import MathCalculator
calc = MathCalculator()
print('✅ Calculator test:', calc.calculate('2+2'))
"

# Test database connection
python -c "
from cli_chatbot import init_db
init_db()
print('✅ Database initialization successful')
"
```

### Security Tests
```bash
# Test secure math evaluation (should fail safely)
python -c "
from cli_chatbot import MathCalculator
calc = MathCalculator()
print('🔒 Security test:', calc.calculate('__import__'))
"
```

## 🚨 Troubleshooting

### Common Issues

**Import Errors:**
```bash
pip install --upgrade cryptography sqlalchemy werkzeug gpt4all
```

**Encryption Key Missing:**
```bash
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

**Database Permissions:**
- Ensure write permissions for `chatbot.db`
- Check SQLite installation
- Verify file system access

**Mathematical Calculator Issues:**
- Expressions must be valid Python syntax
- Use `**` instead of `^` for exponentiation
- Functions require parentheses: `sqrt(16)` not `sqrt 16`

**Executable Distribution Issues:**
- Include all hidden imports in PyInstaller spec
- Test on target platform before distribution
- Whitelist executable with antivirus software
- Ensure all required DLLs are included

**GPT4All Model Issues:**
```bash
# Download required model manually
import gpt4all
model = gpt4all.GPT4All("orca-mini-3b-gguf2.Q4_0.gguf")
```

### Performance Optimization

**For Large Deployments:**
- Use PostgreSQL instead of SQLite
- Enable connection pooling
- Configure appropriate session timeouts
- Monitor memory usage with large chat histories

**For Resource-Constrained Systems:**
- Use smaller GPT4All models
- Reduce chat history retention
- Limit mathematical expression complexity
- Disable AI features if needed

## 📊 Usage Statistics

The application tracks (locally and securely):
- Number of conversations per user
- Mathematical calculations performed
- Discussion topics facilitated
- Negotiation sessions completed
- User preference changes

All data is encrypted and stored locally - no external tracking.

## 🔄 Version History

### Version 2.0 (Current)
- ✨ Added mathematical calculation engine with AST security
- 🤝 Implemented convocation (group discussion) tools
- ⚖️ Added negotiation and conflict resolution features
- 💡 Created intelligent suggestions system
- 🔒 Enhanced security with secure mathematical evaluation
- 📱 Improved cross-platform compatibility

### Version 1.0
- 🤖 Basic AI chatbot functionality
- 🔐 Secure authentication and encryption
- 💾 SQLite database integration
- 🔑 Session management

## 📄 License

This project is provided as-is for educational and personal use. Please respect all applicable licenses for dependencies and AI models.

## 🤝 Contributing

Contributions are welcome! Please focus on:
- Security improvements
- Additional mathematical functions
- Enhanced AI integration
- Cross-platform compatibility
- Documentation improvements

## 📞 Support

For issues and questions:

1. **Check Troubleshooting**: Review the troubleshooting section above
2. **Verify Setup**: Ensure all dependencies are installed correctly
3. **Check Environment**: Verify `ENCRYPTION_KEY` is set properly
4. **Test Incrementally**: Test individual features to isolate issues
5. **Review Logs**: Check console output for specific error messages

## ⚠️ Important Security Notes

- **🔑 Keep your encryption key secure and backed up**
- **💾 Loss of encryption key = loss of all data**
- **🔒 Use strong passwords for user accounts**
- **🛡️ Run only trusted mathematical expressions**
- **📱 Keep the application updated for security patches**

---

**Built with ❤️ using Python, SQLAlchemy, Cryptography, and GPT4All**

*This comprehensive AI chatbot combines secure local processing with advanced conversational features for a complete CLI experience.*#   C h a t B o t 
 
 
