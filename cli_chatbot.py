#!/usr/bin/env python3
"""
CLI-based Local AI Chatbot
Secure command-line chatbot with local authentication and encrypted storage
"""
import os
import sys
import getpass
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import json

# Database setup
Base = declarative_base()

# Encryption setup
def get_encryption_key():
    """Get encryption key for data at rest"""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is required for data encryption. Please set this securely.")
    return key.encode() if isinstance(key, str) else key

cipher_suite = Fernet(get_encryption_key())

class User(Base):
    """User model with local authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_history = relationship('ChatHistory', back_populates='user', cascade='all, delete-orphan')
    preferences = relationship('UserPreferences', back_populates='user', cascade='all, delete-orphan', uselist=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        if password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if password and self.password_hash is not None:
            return check_password_hash(str(self.password_hash), password)
        return False
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()

class UserPreferences(Base):
    """User personalization preferences"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Encrypted preference data
    _preferences_data = Column('preferences_data', Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='preferences')
    
    @property
    def preferences_data(self):
        """Decrypt and return preferences data"""
        if self._preferences_data is not None:
            try:
                decrypted = cipher_suite.decrypt(str(self._preferences_data).encode()).decode()
                return json.loads(decrypted)
            except Exception:
                return {}
        return {}
    
    @preferences_data.setter
    def preferences_data(self, value):
        """Encrypt and store preferences data"""
        if value:
            json_str = json.dumps(value)
            encrypted = cipher_suite.encrypt(json_str.encode()).decode()
            self._preferences_data = encrypted
        else:
            self._preferences_data = None
    
    def get_preference(self, key, default=None):
        """Get a specific preference value"""
        return self.preferences_data.get(key, default)
    
    def set_preference(self, key, value):
        """Set a specific preference value"""
        prefs = self.preferences_data
        prefs[key] = value
        self.preferences_data = prefs
        self.updated_at = datetime.utcnow()

class ChatHistory(Base):
    """Encrypted chat history for each user"""
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Encrypted message content
    _user_message = Column('user_message', Text)
    _bot_response = Column('bot_response', Text)
    
    # Metadata
    conversation_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship('User', back_populates='chat_history')
    
    @property
    def user_message(self):
        """Decrypt and return user message"""
        if self._user_message is not None:
            try:
                return cipher_suite.decrypt(str(self._user_message).encode()).decode()
            except Exception:
                return "[Decryption Error]"
        return ""
    
    @user_message.setter
    def user_message(self, value):
        """Encrypt and store user message"""
        if value:
            encrypted = cipher_suite.encrypt(value.encode()).decode()
            self._user_message = encrypted
    
    @property
    def bot_response(self):
        """Decrypt and return bot response"""
        if self._bot_response is not None:
            try:
                return cipher_suite.decrypt(str(self._bot_response).encode()).decode()
            except Exception:
                return "[Decryption Error]"
        return ""
    
    @bot_response.setter
    def bot_response(self, value):
        """Encrypt and store bot response"""
        if value:
            encrypted = cipher_suite.encrypt(value.encode()).decode()
            self._bot_response = encrypted
    
    def __repr__(self):
        return f'<ChatHistory User:{self.user_id} at {self.timestamp}>'

# Local LLM integration
try:
    from gpt4all import GPT4All
    LLM_AVAILABLE = True
except ImportError:
    GPT4All = None
    LLM_AVAILABLE = False
    print("Warning: GPT4All not available. Using mock responses.")

class ChatbotEngine:
    """Local LLM chatbot engine with memory and personalization"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        
    def load_model(self):
        """Load the local LLM model"""
        if not LLM_AVAILABLE:
            return False
            
        try:
            if LLM_AVAILABLE and GPT4All is not None:
                self.model = GPT4All("Llama-3.2-1B-Instruct-Q4_0.gguf")
                self.model_loaded = True
                print("Local LLM model loaded successfully!")
                return True
        except Exception as e:
            print(f"Failed to load LLM model: {e}")
            return False
        return False
    
    def generate_response(self, message, user_context=None, conversation_history=None):
        """Generate chatbot response with context and memory"""
        if not self.model_loaded and LLM_AVAILABLE:
            self.load_model()
        
        # Build context from user preferences and history
        context = self._build_context(user_context, conversation_history)
        
        # Create the prompt with context
        prompt = f"{context}\n\nUser: {message}\nAssistant:"
        
        if self.model_loaded and self.model:
            try:
                response = self.model.generate(prompt, max_tokens=200, temp=0.7)
                return response.strip()
            except Exception as e:
                print(f"LLM generation error: {e}")
                return self._get_fallback_response(message, user_context)
        else:
            return self._get_fallback_response(message, user_context)
    
    def _build_context(self, user_context, conversation_history):
        """Build context string from user data and history"""
        context_parts = []
        
        if user_context:
            name = user_context.get("display_name", "User")
            style = user_context.get("chat_style", "friendly")
            interests = user_context.get("topics_of_interest", [])
            
            context_parts.append(f"You are a helpful AI assistant. Be {style} and direct.")
            
            if interests:
                context_parts.append(f"The user likes: {', '.join(interests)}.")
        
        # Add conversation context without labels to avoid repetition in responses
        if conversation_history and len(conversation_history) > 0:
            context_parts.append("Previous context:")
            for entry in reversed(conversation_history[-2:]):  # Only last 2 for cleaner context
                context_parts.append(f"Q: {entry.user_message}")
                context_parts.append(f"A: {entry.bot_response}")
        
        return "\n".join(context_parts)
    
    def _get_fallback_response(self, message, user_context=None):
        """Fallback responses when LLM is not available"""
        name = user_context.get("display_name", "there") if user_context else "there"
        
        fallback_responses = [
            f"Hi {name}! I'm currently running in demo mode. In the full version, I would use a local LLM to provide intelligent responses to your message: '{message}'",
            f"Hello {name}! I understand you said: '{message}'. I'm designed to remember our conversation and your preferences for personalized responses.",
            f"Thanks for your message, {name}! While I'm in demo mode, I would normally analyze your message and provide contextual responses based on our chat history.",
        ]
        
        # Simple keyword-based responses for demonstration
        message_lower = message.lower()
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return f"Hello {name}! How can I help you today?"
        elif any(word in message_lower for word in ["bye", "goodbye", "see you"]):
            return f"Goodbye {name}! It was great chatting with you. Your conversation is safely stored and encrypted."
        elif "help" in message_lower:
            return f"I'm here to help, {name}! You can ask me anything, and I'll remember our conversation for future reference."
        else:
            return fallback_responses[hash(message) % len(fallback_responses)]

class CLIChatbot:
    """Main CLI Chatbot Application"""
    
    def __init__(self):
        self.setup_database()
        self.current_user = None
        self.chatbot_engine = ChatbotEngine()
        
    def setup_database(self):
        """Initialize database connection and create tables"""
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("Warning: DATABASE_URL not found. Using SQLite.")
            database_url = 'sqlite:///chatbot.db'
        
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def run(self):
        """Main application loop"""
        print("🤖 Welcome to Local AI Chatbot (CLI Mode)")
        print("=" * 50)
        
        while True:
            if not self.current_user:
                choice = self.auth_menu()
                if choice == '3':
                    print("Goodbye!")
                    break
            else:
                choice = self.main_menu()
                if choice == '4':
                    self.logout()
                elif choice == '5':
                    print("Goodbye!")
                    break
    
    def auth_menu(self):
        """Authentication menu"""
        print("\n--- Authentication ---")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        
        while True:
            choice = input("\nSelect option (1-3): ").strip()
            if choice == '1':
                self.login()
                return choice
            elif choice == '2':
                self.register()
                return choice
            elif choice == '3':
                return choice
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def main_menu(self):
        """Main application menu"""
        if self.current_user is None:
            return '3'  # Exit if no user
        print(f"\n--- Welcome {self.current_user.username}! ---")
        print("1. Start Chat")
        print("2. View Chat History")
        print("3. Manage Preferences")
        print("4. Logout")
        print("5. Exit")
        
        while True:
            choice = input("\nSelect option (1-5): ").strip()
            if choice == '1':
                self.start_chat()
                return choice
            elif choice == '2':
                self.view_chat_history()
                return choice
            elif choice == '3':
                self.manage_preferences()
                return choice
            elif choice in ['4', '5']:
                return choice
            else:
                print("Invalid choice. Please enter 1-5.")
    
    def login(self):
        """User login"""
        print("\n--- Login ---")
        username = input("Username: ").strip()
        if not username:
            print("Username cannot be empty.")
            return
        
        password = getpass.getpass("Password: ")
        if not password:
            print("Password cannot be empty.")
            return
        
        user = self.session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            self.current_user = user
            user.update_last_login()
            self.session.commit()
            print(f"✅ Welcome back, {user.username}!")
        else:
            print("❌ Invalid username or password.")
    
    def register(self):
        """User registration"""
        print("\n--- Register ---")
        username = input("Username: ").strip()
        if not username:
            print("Username cannot be empty.")
            return
        
        # Check if username exists
        if self.session.query(User).filter_by(username=username).first():
            print("❌ Username already exists.")
            return
        
        email = input("Email: ").strip()
        if not email:
            print("Email cannot be empty.")
            return
        
        # Check if email exists
        if self.session.query(User).filter_by(email=email).first():
            print("❌ Email already registered.")
            return
        
        password = getpass.getpass("Password (min 6 chars): ")
        if not password or len(password) < 6:
            print("❌ Password must be at least 6 characters.")
            return
        
        confirm_password = getpass.getpass("Confirm Password: ")
        if password != confirm_password:
            print("❌ Passwords do not match.")
            return
        
        # Create new user
        user = User(
            username=username,
            email=email
        )
        user.set_password(password)
        
        self.session.add(user)
        self.session.flush()
        
        # Create default preferences  
        preferences = UserPreferences(
            user_id=user.id
        )
        preferences.preferences_data = {
            "display_name": username,
            "chat_style": "friendly",
            "topics_of_interest": [],
            "response_length": "medium"
        }
        self.session.add(preferences)
        self.session.commit()
        
        print(f"✅ Account created successfully! Welcome, {username}!")
        self.current_user = user
    
    def start_chat(self):
        """Start chat session"""
        print("\n--- AI Chat Session ---")
        print("Type 'quit' to return to main menu")
        print("🔒 All messages are encrypted and stored securely")
        print("-" * 50)
        
        conversation_id = str(uuid.uuid4())
        
        while True:
            try:
                if self.current_user is None:
                    break
                user_message = input(f"\n{self.current_user.username}: ").strip()
                if not user_message:
                    continue
                
                if user_message.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Get user preferences for personalization
                user_prefs = self.current_user.preferences
                user_context = user_prefs.preferences_data if user_prefs else {}
                
                # Get recent conversation history for context (limit to 3 for cleaner context)
                recent_history = self.session.query(ChatHistory)\
                    .filter_by(user_id=self.current_user.id)\
                    .order_by(ChatHistory.timestamp.desc())\
                    .limit(3).all()
                
                print("🤖 AI is thinking...")
                
                # Generate bot response
                bot_response = self.chatbot_engine.generate_response(
                    user_message, 
                    user_context=user_context,
                    conversation_history=recent_history
                )
                
                print(f"🤖 AI: {bot_response}")
                
                # Save to database with encryption
                if self.current_user is None:
                    break
                chat_entry = ChatHistory(
                    user_id=self.current_user.id,
                    conversation_id=conversation_id
                )
                chat_entry.user_message = user_message
                chat_entry.bot_response = bot_response
                
                self.session.add(chat_entry)
                self.session.commit()
                
            except KeyboardInterrupt:
                print("\n\nChat session ended.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def view_chat_history(self):
        """View chat history"""
        print("\n--- Chat History ---")
        
        if self.current_user is None:
            print("No user logged in.")
            return
        history = self.session.query(ChatHistory)\
            .filter_by(user_id=self.current_user.id)\
            .order_by(ChatHistory.timestamp.desc())\
            .limit(20).all()
        
        if not history:
            print("No chat history found.")
            return
        
        print(f"Last 20 conversations (Total messages: {len(history)})")
        print("-" * 70)
        
        for entry in reversed(history):  # Show oldest first
            print(f"\n[{entry.timestamp.strftime('%Y-%m-%d %H:%M')}]")
            print(f"You: {entry.user_message}")
            print(f"AI:  {entry.bot_response}")
        
        input("\nPress Enter to continue...")
    
    def manage_preferences(self):
        """Manage user preferences"""
        print("\n--- Manage Preferences ---")
        
        if self.current_user is None:
            print("No user logged in.")
            return
        prefs = self.current_user.preferences
        if not prefs:
            prefs = UserPreferences(
                user_id=self.current_user.id
            )
            prefs.preferences_data = {
                "display_name": str(self.current_user.username),
                "chat_style": "friendly",
                "topics_of_interest": [],
                "response_length": "medium"
            }
            self.session.add(prefs)
            self.session.commit()
        
        while True:
            print(f"\nCurrent Preferences:")
            print(f"1. Display Name: {prefs.get_preference('display_name', self.current_user.username if self.current_user else 'User')}")
            print(f"2. Chat Style: {prefs.get_preference('chat_style', 'friendly')}")
            print(f"3. Response Length: {prefs.get_preference('response_length', 'medium')}")
            print(f"4. Topics of Interest: {', '.join(prefs.get_preference('topics_of_interest', []))}")
            print("5. Return to Main Menu")
            
            choice = input("\nSelect option to modify (1-5): ").strip()
            
            if choice == '1':
                new_name = input("Enter new display name: ").strip()
                if new_name:
                    prefs.set_preference('display_name', new_name)
                    self.session.commit()
                    print("✅ Display name updated!")
            
            elif choice == '2':
                print("Chat Styles: friendly, professional, humorous, concise, detailed")
                new_style = input("Enter chat style: ").strip().lower()
                if new_style in ['friendly', 'professional', 'humorous', 'concise', 'detailed']:
                    prefs.set_preference('chat_style', new_style)
                    self.session.commit()
                    print("✅ Chat style updated!")
                else:
                    print("❌ Invalid chat style.")
            
            elif choice == '3':
                print("Response Lengths: short, medium, long")
                new_length = input("Enter response length: ").strip().lower()
                if new_length in ['short', 'medium', 'long']:
                    prefs.set_preference('response_length', new_length)
                    self.session.commit()
                    print("✅ Response length updated!")
                else:
                    print("❌ Invalid response length.")
            
            elif choice == '4':
                print("Enter topics separated by commas (e.g., technology, science, programming)")
                topics_input = input("Topics: ").strip()
                if topics_input:
                    topics = [topic.strip() for topic in topics_input.split(',')]
                    prefs.set_preference('topics_of_interest', topics)
                    self.session.commit()
                    print("✅ Topics updated!")
            
            elif choice == '5':
                break
            
            else:
                print("❌ Invalid choice.")
    
    def logout(self):
        """Logout current user"""
        if self.current_user is None:
            print("No user logged in.")
            return
        username = self.current_user.username
        self.current_user = None
        print(f"✅ Goodbye {username}! You have been logged out.")

def main():
    """Main entry point"""
    try:
        app = CLIChatbot()
        app.run()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user.")
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()