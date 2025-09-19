#!/usr/bin/env python3
"""
CLI-based Local AI Chatbot
Secure command-line chatbot with local authentication and encrypted storage
"""
import os
import sys
import getpass
import uuid
import re
import math
import ast
import operator
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

class MathCalculator:
    """Secure mathematical calculation engine using AST parsing"""
    
    def __init__(self):
        # Safe binary operations
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Safe mathematical functions
        self.functions = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'pow': pow,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'floor': math.floor,
            'ceil': math.ceil,
            'factorial': math.factorial,
            'radians': math.radians,
            'degrees': math.degrees,
        }
        
        # Mathematical constants
        self.constants = {
            'pi': math.pi,
            'e': math.e,
        }
        
        # Maximum input length to prevent DoS
        self.MAX_INPUT_LENGTH = 1000
        self.MAX_NUMBER = 10**10  # Reasonable limits
    
    def is_math_expression(self, text):
        """Check if text contains a mathematical expression by attempting safe parsing"""
        if not text or len(text) > self.MAX_INPUT_LENGTH:
            return False
            
        text = text.strip()
        
        # Quick early filtering - avoid parsing complex text
        if len(text.split()) > 10:  # Likely sentence, not math
            return False
            
        # Must have mathematical indicators
        has_numbers = bool(re.search(r'\d', text))
        has_operators = bool(re.search(r'[+\-*/^%()\*\*]', text))  # Removed dot
        has_functions = any(func in text.lower() for func in self.functions.keys())
        has_constants = any(const in text.lower() for const in self.constants.keys())
        
        if not ((has_numbers or has_constants) and (has_operators or has_functions)):
            return False
        
        # Test if it can be parsed as a valid math expression
        try:
            expr = text.replace('^', '**').replace('×', '*').replace('÷', '/').replace('√', 'sqrt')
            tree = ast.parse(expr, mode='eval')
            
            # Check for forbidden nodes
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute, 
                                   ast.Subscript, ast.ListComp, ast.DictComp, 
                                   ast.SetComp, ast.GeneratorExp, ast.Lambda,
                                   ast.Dict, ast.List, ast.Set, ast.Tuple)):
                    return False
            
            return True
        except (SyntaxError, ValueError):
            return False
    
    def _safe_eval(self, node):
        """Safely evaluate an AST node"""
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        elif isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                if abs(node.value) > self.MAX_NUMBER:
                    raise ValueError("Number too large")
                return node.value
            else:
                raise ValueError("Invalid constant type")
        elif isinstance(node, ast.Num):  # Python < 3.8
            if abs(node.n) > self.MAX_NUMBER:
                raise ValueError("Number too large")
            return node.n
        elif isinstance(node, ast.Name):
            if node.id in self.constants:
                return self.constants[node.id]
            else:
                raise ValueError(f"Unknown variable: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op = self.operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            
            # Special handling for division by zero and power limits
            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("Division by zero")
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Power exponent too large")
                
            result = op(left, right)
            if abs(result) > self.MAX_NUMBER:
                raise ValueError("Result too large")
            return result
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op = self.operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operation: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Invalid function call")
            func_name = node.func.id
            if func_name not in self.functions:
                raise ValueError(f"Unknown function: {func_name}")
            
            args = [self._safe_eval(arg) for arg in node.args]
            
            # Special handling to prevent DoS attacks
            if func_name == 'factorial':
                if len(args) != 1 or not isinstance(args[0], int) or args[0] < 0 or args[0] > 100:
                    raise ValueError("Factorial argument must be a non-negative integer ≤ 100")
            elif func_name == 'pow':
                if len(args) == 2:  # pow(base, exponent)
                    base, exponent = args
                    if abs(base) > self.MAX_NUMBER or abs(exponent) > 100:
                        raise ValueError("Power base/exponent too large")
                elif len(args) == 3:  # pow(base, exponent, modulus)
                    base, exponent, modulus = args
                    if abs(base) > self.MAX_NUMBER or abs(modulus) > self.MAX_NUMBER:
                        raise ValueError("Power arguments too large")
                    if abs(exponent) > 10000:  # Allow larger exponents for modular pow
                        raise ValueError("Power exponent too large")
                else:
                    raise ValueError("pow() takes 2 or 3 arguments")
            elif func_name in ('round', 'min', 'max'):
                if len(args) == 0:
                    raise ValueError(f"{func_name}() requires at least 1 argument")
                # Allow these functions but check argument bounds
                for arg in args:
                    if isinstance(arg, (int, float)) and abs(arg) > self.MAX_NUMBER:
                        raise ValueError("Argument too large")
            
            # Handle keyword arguments (currently not supported)
            if node.keywords:
                raise ValueError("Keyword arguments not supported")
            
            result = self.functions[func_name](*args)
            if isinstance(result, (int, float)) and abs(result) > self.MAX_NUMBER:
                raise ValueError("Function result too large")
            return result
        else:
            raise ValueError(f"Unsupported AST node: {type(node).__name__}")
    
    def calculate(self, expression):
        """Safely calculate mathematical expressions using AST parsing"""
        try:
            if not expression or len(expression) > self.MAX_INPUT_LENGTH:
                return "Error: Expression too long or empty"
            
            # Clean the expression
            expr = expression.strip()
            
            # Replace common symbols
            expr = expr.replace('^', '**')  # Power operator
            expr = expr.replace('×', '*')   # Multiplication symbol
            expr = expr.replace('÷', '/')   # Division symbol
            expr = expr.replace('√', 'sqrt') # Square root symbol
            
            # Parse the expression into an AST
            try:
                tree = ast.parse(expr, mode='eval')
            except SyntaxError as e:
                return f"Syntax Error: {str(e)}"
            
            # Check for dangerous nodes
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute, 
                                   ast.Subscript, ast.ListComp, ast.DictComp, 
                                   ast.SetComp, ast.GeneratorExp, ast.Lambda,
                                   ast.Dict, ast.List, ast.Set, ast.Tuple)):
                    return "Error: Unsupported operation"
            
            # Evaluate safely
            result = self._safe_eval(tree)
            
            # Format result nicely
            if isinstance(result, float):
                if math.isnan(result):
                    return "Error: Result is not a number"
                elif math.isinf(result):
                    return "Error: Result is infinite"
                elif result.is_integer():
                    return str(int(result))
                else:
                    return f"{result:.10g}"  # Remove trailing zeros
            return str(result)
            
        except ValueError as e:
            return f"Math Error: {str(e)}"
        except Exception as e:
            return f"Calculation Error: {str(e)}"
    
    def get_math_help(self):
        """Return help text for mathematical operations"""
        return (
            "🧮 **Mathematical Calculator Help**\n\n"
            "**Basic Operations:**\n"
            "• Addition: 5 + 3\n"
            "• Subtraction: 10 - 4\n" 
            "• Multiplication: 6 * 7 (or 6×7)\n"
            "• Division: 15 / 3 (or 15÷3)\n"
            "• Power: 2^3 or 2**3\n"
            "• Modulo: 17 % 5\n\n"
            "**Advanced Functions:**\n"
            "• Square root: sqrt(25)\n"
            "• Trigonometry: sin(pi/2), cos(0), tan(pi/4)\n"
            "• Logarithms: log(10), log10(100)\n"
            "• Exponential: exp(1)\n"
            "• Factorial: factorial(5)\n"
            "• Rounding: round(3.14159, 2), floor(4.8), ceil(4.1)\n\n"
            "**Constants:**\n"
            "• pi = 3.14159...\n"
            "• e = 2.71828...\n\n"
            "**Examples:**\n"
            "• sqrt(16) + 5\n"
            "• sin(pi/6) * 2\n"
            "• log10(1000) + factorial(4)\n"
            "• (2^3 + 4) * sqrt(9)"
        )

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

# Gemini AI integration
try:
    from google import genai
    from google.genai import types
    import os
    GEMINI_AVAILABLE = True
    # Initialize Gemini client
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        gemini_client = genai.Client(api_key=api_key)
    else:
        gemini_client = None
        GEMINI_AVAILABLE = False
        print("Warning: GEMINI_API_KEY not found. Using fallback responses.")
except ImportError:
    GEMINI_AVAILABLE = False
    gemini_client = None
    types = None
    print("Warning: Gemini not available. Using fallback responses.")

class ChatbotEngine:
    """Gemini AI chatbot engine with memory and personalization"""
    
    def __init__(self):
        self.ready = GEMINI_AVAILABLE and gemini_client is not None
        self.math_calculator = MathCalculator()
        if self.ready:
            print("Gemini AI ready for fast responses!")
        print("🧮 Mathematical calculator ready!")
        
    def load_model(self):
        """Check if Gemini API is ready (no model loading needed)"""
        return self.ready
    
    def generate_response(self, message, user_context=None, conversation_history=None):
        """Generate chatbot response using Gemini API with math calculation support"""
        # Check for mathematical expressions first
        if self.math_calculator.is_math_expression(message):
            result = self.math_calculator.calculate(message)
            name = user_context.get("display_name", "there") if user_context else "there"
            return f"🧮 {name}, the answer is: **{result}**"
        
        if not self.ready or not gemini_client:
            return self._get_fallback_response(message, user_context)
        
        try:
            # Build context for better responses
            context = self._build_context(user_context, conversation_history)
            
            # Create system instruction for Gemini
            system_instruction = f"{context}\n\nProvide helpful, accurate, and direct responses. If the user asks for mathematical calculations, perform them accurately."
            
            # Generate response using Gemini
            if types:
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Content(role="user", parts=[types.Part(text=message)])
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        max_output_tokens=300,
                        temperature=0.7
                    )
                )
            else:
                return self._get_fallback_response(message, user_context)
            
            if response and response.text:
                return response.text.strip()
            else:
                return self._get_fallback_response(message, user_context)
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._get_fallback_response(message, user_context)
    
    def _build_context(self, user_context, conversation_history):
        """Build context string from user data and history"""
        context_parts = []
        
        if user_context:
            style = user_context.get("chat_style", "friendly")
            interests = user_context.get("topics_of_interest", [])
            
            context_parts.append(f"Be {style} and direct in your responses.")
            
            if interests:
                context_parts.append(f"User interests: {', '.join(interests)}.")
        
        # Minimal history context for continuity without repetition
        if conversation_history and len(conversation_history) > 0:
            last_entry = conversation_history[0]  # Most recent
            context_parts.append(f"Previous exchange - User: {last_entry.user_message[:50]}...")
        
        return " ".join(context_parts)
    
    def _get_fallback_response(self, message, user_context=None):
        """Fallback responses when LLM is not available"""
        name = user_context.get("display_name", "there") if user_context else "there"
        
        # Check for mathematical expressions first
        if self.math_calculator.is_math_expression(message):
            result = self.math_calculator.calculate(message)
            return f"🧮 {name}, the answer is: **{result}**"
        
        fallback_responses = [
            f"Hi {name}! I'm currently running in demo mode. In the full version, I would use a local LLM to provide intelligent responses to your message: '{message}'",
            f"Hello {name}! I understand you said: '{message}'. I'm designed to remember our conversation and your preferences for personalized responses.",
            f"Thanks for your message, {name}! While I'm in demo mode, I would normally analyze your message and provide contextual responses based on our chat history.",
        ]
        
        # Simple keyword-based responses for demonstration
        message_lower = message.lower()
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return f"Hello {name}! How can I help you today? I can also do mathematical calculations like 2+2 or sqrt(16)!"
        elif any(word in message_lower for word in ["bye", "goodbye", "see you"]):
            return f"Goodbye {name}! It was great chatting with you. Your conversation is safely stored and encrypted."
        elif "help" in message_lower:
            return f"I'm here to help, {name}! You can ask me anything, and I'll remember our conversation for future reference. I can also calculate mathematical expressions!"
        elif any(word in message_lower for word in ["math", "calculate", "calculator"]):
            return f"🧮 {name}! I can help with mathematical calculations. Try expressions like:\n• Basic: 15 + 27, 100 / 4, 2^8\n• Advanced: sqrt(144), sin(pi/2), log10(1000)\n• Or ask me for more math help!"
        else:
            return fallback_responses[hash(message) % len(fallback_responses)]
    
    def facilitate_convocation(self, topic, perspectives=None, user_context=None):
        """Facilitate group discussion by gathering multiple perspectives on a topic"""
        context = "You are an expert facilitator helping to convene a thoughtful discussion. "
        if user_context:
            style = user_context.get("chat_style", "professional")
            context += f"Maintain a {style} tone. "
        
        prompt = f"Topic for convocation: '{topic}'\n\n"
        
        if perspectives:
            prompt += f"Existing perspectives to consider: {', '.join(perspectives)}\n\n"
        
        prompt += ("Please help facilitate this discussion by:\n"
                  "1. Presenting multiple valid viewpoints on this topic\n"
                  "2. Identifying key questions that need to be addressed\n"
                  "3. Suggesting a structured approach to explore the topic\n"
                  "4. Highlighting potential areas of common ground\n"
                  "5. Proposing next steps for productive dialogue")
        
        system_instruction = context + "Act as a skilled facilitator bringing people together around important topics."
        
        return self._generate_specialized_response(prompt, system_instruction, user_context)
    
    def assist_negotiation(self, situation, parties=None, constraints=None, user_context=None):
        """Help with negotiation by analyzing positions and suggesting win-win solutions"""
        context = "You are an expert negotiation advisor helping to reach mutually beneficial agreements. "
        if user_context:
            style = user_context.get("chat_style", "professional") 
            context += f"Maintain a {style} but diplomatic tone. "
        
        prompt = f"Negotiation situation: '{situation}'\n\n"
        
        if parties:
            prompt += f"Parties involved: {', '.join(parties)}\n"
        if constraints:
            prompt += f"Known constraints: {', '.join(constraints)}\n\n"
        
        prompt += ("Please help with this negotiation by:\n"
                  "1. Analyzing the underlying interests of each party\n"
                  "2. Identifying potential areas for mutual benefit\n"
                  "3. Suggesting creative solutions that address core needs\n"
                  "4. Proposing a framework for productive discussions\n"
                  "5. Highlighting potential pitfalls to avoid\n"
                  "6. Recommending specific negotiation strategies")
        
        system_instruction = context + "Focus on win-win outcomes and building lasting agreements."
        
        return self._generate_specialized_response(prompt, system_instruction, user_context)
    
    def provide_suggestions(self, problem_area, goals=None, context_info=None, user_context=None):
        """Provide useful, actionable suggestions for specific problems or goals"""
        context = "You are a knowledgeable advisor providing practical, actionable suggestions. "
        if user_context:
            style = user_context.get("chat_style", "helpful")
            interests = user_context.get("topics_of_interest", [])
            context += f"Be {style} in your approach. "
            if interests:
                context += f"Consider the user's interests in: {', '.join(interests)}. "
        
        prompt = f"Area needing suggestions: '{problem_area}'\n\n"
        
        if goals:
            prompt += f"Desired outcomes: {goals}\n"
        if context_info:
            prompt += f"Additional context: {context_info}\n\n"
        
        prompt += ("Please provide useful suggestions by:\n"
                  "1. Breaking down the challenge into manageable components\n"
                  "2. Offering specific, actionable recommendations\n"
                  "3. Prioritizing suggestions by impact and feasibility\n"
                  "4. Explaining the reasoning behind key recommendations\n"
                  "5. Identifying potential obstacles and how to overcome them\n"
                  "6. Suggesting metrics to measure progress\n"
                  "7. Providing both short-term and long-term strategies")
        
        system_instruction = context + "Focus on practical, implementable advice that creates real value."
        
        return self._generate_specialized_response(prompt, system_instruction, user_context)
    
    def _generate_specialized_response(self, prompt, system_instruction, user_context):
        """Generate response for specialized features using AI or fallback"""
        if not self.ready or not gemini_client:
            return self._get_specialized_fallback(prompt, user_context)
        
        try:
            if types:
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Content(role="user", parts=[types.Part(text=prompt)])
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        max_output_tokens=600,
                        temperature=0.8
                    )
                )
                
                if response and response.text:
                    return response.text.strip()
            
            return self._get_specialized_fallback(prompt, user_context)
            
        except Exception as e:
            print(f"AI API error: {e}")
            return self._get_specialized_fallback(prompt, user_context)
    
    def _get_specialized_fallback(self, prompt, user_context):
        """Fallback responses for specialized features"""
        name = user_context.get("display_name", "there") if user_context else "there"
        
        if "convocation" in prompt.lower() or "facilitate" in prompt.lower():
            return (f"Hello {name}! I can help facilitate discussions by gathering different perspectives. "
                   f"While in demo mode, I would analyze your topic and provide structured approaches "
                   f"for productive group conversations, identify key questions to explore, and suggest "
                   f"ways to find common ground between different viewpoints.")
        
        elif "negotiation" in prompt.lower() or "parties" in prompt.lower():
            return (f"Hi {name}! I can assist with negotiations by analyzing interests of all parties "
                   f"and suggesting win-win solutions. In full mode, I would help you understand "
                   f"underlying motivations, identify mutual benefits, and provide strategic frameworks "
                   f"for reaching beneficial agreements.")
        
        else:  # Suggestions
            return (f"Hello {name}! I can provide practical suggestions and actionable advice. "
                   f"With full AI capabilities, I would break down your challenge, prioritize solutions "
                   f"by impact, explain the reasoning behind recommendations, and provide both "
                   f"immediate steps and long-term strategies to help you succeed.")

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
                if choice == '8':
                    self.logout()
                elif choice == '9':
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
            return '9'  # Exit if no user
        print(f"\n--- Welcome {self.current_user.username}! ---")
        print("1. Start Chat")
        print("2. View Chat History")
        print("3. 🧮 Mathematical Calculator")
        print("4. Facilitate Discussion (Convocation)")
        print("5. Negotiate & Resolve (Negotiation)")
        print("6. Get Smart Suggestions")
        print("7. Manage Preferences")
        print("8. Logout")
        print("9. Exit")
        
        while True:
            choice = input("\nSelect option (1-9): ").strip()
            if choice == '1':
                self.start_chat()
                return choice
            elif choice == '2':
                self.view_chat_history()
                return choice
            elif choice == '3':
                self.calculator_session()
                return choice
            elif choice == '4':
                self.convocation_session()
                return choice
            elif choice == '5':
                self.negotiation_session()
                return choice
            elif choice == '6':
                self.suggestion_session()
                return choice
            elif choice == '7':
                self.manage_preferences()
                return choice
            elif choice in ['8', '9']:
                return choice
            else:
                print("Invalid choice. Please enter 1-9.")
    
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
                
                print("🤖 Generating response...")
                
                # Generate bot response with Gemini
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
    
    def calculator_session(self):
        """Interactive mathematical calculator session"""
        print("\n--- 🧮 Mathematical Calculator ---")
        print("Enter mathematical expressions to calculate")
        print("Type 'help' for examples, or 'quit' to return to main menu")
        print("-" * 50)
        
        if self.current_user is None:
            print("No user logged in.")
            return
        
        conversation_id = str(uuid.uuid4())
        
        while True:
            try:
                expression = input(f"\n🧮 Math: ").strip()
                
                if not expression:
                    continue
                
                if expression.lower() in ['quit', 'exit', 'q']:
                    break
                
                if expression.lower() == 'help':
                    help_text = self.chatbot_engine.math_calculator.get_math_help()
                    print(f"\n{help_text}")
                    continue
                
                # Calculate the expression
                result = self.chatbot_engine.math_calculator.calculate(expression)
                
                print(f"🧮 Result: {result}")
                
                # Save to chat history
                chat_entry = ChatHistory(
                    user_id=self.current_user.id,
                    conversation_id=conversation_id
                )
                chat_entry.user_message = f"[CALCULATOR] {expression}"
                chat_entry.bot_response = f"Result: {result}"
                
                self.session.add(chat_entry)
                self.session.commit()
                
            except KeyboardInterrupt:
                print("\n\nCalculator session ended.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")

    def convocation_session(self):
        """Facilitate group discussion session"""
        print("\n--- 🤝 Facilitate Discussion (Convocation) ---")
        print("Help bring people together around important topics")
        
        if self.current_user is None:
            print("No user logged in.")
            return
            
        topic = input("\nWhat topic would you like to facilitate discussion around? ").strip()
        if not topic:
            print("❌ Topic cannot be empty.")
            return
        
        perspectives_input = input("Any existing perspectives to consider? (comma-separated, or press Enter to skip): ").strip()
        perspectives = [p.strip() for p in perspectives_input.split(',')] if perspectives_input else None
        
        print("\n🤖 Analyzing topic and preparing facilitation framework...")
        
        # Get user preferences for personalization
        user_prefs = self.current_user.preferences
        user_context = user_prefs.preferences_data if user_prefs else {}
        
        # Generate convocation response
        response = self.chatbot_engine.facilitate_convocation(
            topic=topic,
            perspectives=perspectives,
            user_context=user_context
        )
        
        print(f"\n🤖 Convocation Facilitator:\n{response}")
        
        # Save the session to chat history
        conversation_id = str(uuid.uuid4())
        chat_entry = ChatHistory(
            user_id=self.current_user.id,
            conversation_id=conversation_id
        )
        chat_entry.user_message = f"[CONVOCATION] Topic: {topic}" + (f" | Perspectives: {', '.join(perspectives)}" if perspectives else "")
        chat_entry.bot_response = response
        
        self.session.add(chat_entry)
        self.session.commit()
        
        input("\nPress Enter to continue...")
    
    def negotiation_session(self):
        """Assist with negotiation and conflict resolution"""
        print("\n--- ⚖️ Negotiate & Resolve (Negotiation Assistant) ---")
        print("Help reach mutually beneficial agreements")
        
        if self.current_user is None:
            print("No user logged in.")
            return
            
        situation = input("\nDescribe the negotiation situation: ").strip()
        if not situation:
            print("❌ Situation description cannot be empty.")
            return
        
        parties_input = input("Who are the parties involved? (comma-separated, or press Enter to skip): ").strip()
        parties = [p.strip() for p in parties_input.split(',')] if parties_input else None
        
        constraints_input = input("Any known constraints or limitations? (comma-separated, or press Enter to skip): ").strip()
        constraints = [c.strip() for c in constraints_input.split(',')] if constraints_input else None
        
        print("\n🤖 Analyzing negotiation dynamics and generating strategies...")
        
        # Get user preferences for personalization
        user_prefs = self.current_user.preferences
        user_context = user_prefs.preferences_data if user_prefs else {}
        
        # Generate negotiation response
        response = self.chatbot_engine.assist_negotiation(
            situation=situation,
            parties=parties,
            constraints=constraints,
            user_context=user_context
        )
        
        print(f"\n🤖 Negotiation Advisor:\n{response}")
        
        # Save the session to chat history
        conversation_id = str(uuid.uuid4())
        chat_entry = ChatHistory(
            user_id=self.current_user.id,
            conversation_id=conversation_id
        )
        parties_str = f" | Parties: {', '.join(parties)}" if parties else ""
        constraints_str = f" | Constraints: {', '.join(constraints)}" if constraints else ""
        chat_entry.user_message = f"[NEGOTIATION] Situation: {situation}{parties_str}{constraints_str}"
        chat_entry.bot_response = response
        
        self.session.add(chat_entry)
        self.session.commit()
        
        input("\nPress Enter to continue...")
    
    def suggestion_session(self):
        """Provide useful suggestions and recommendations"""
        print("\n--- 💡 Get Smart Suggestions ---")
        print("Get practical, actionable advice for your challenges")
        
        if self.current_user is None:
            print("No user logged in.")
            return
            
        problem_area = input("\nWhat area do you need suggestions for? ").strip()
        if not problem_area:
            print("❌ Problem area cannot be empty.")
            return
        
        goals = input("What are your desired outcomes? (optional): ").strip()
        goals = goals if goals else None
        
        context_info = input("Any additional context that might help? (optional): ").strip()
        context_info = context_info if context_info else None
        
        print("\n🤖 Analyzing your challenge and generating practical suggestions...")
        
        # Get user preferences for personalization
        user_prefs = self.current_user.preferences
        user_context = user_prefs.preferences_data if user_prefs else {}
        
        # Generate suggestions response
        response = self.chatbot_engine.provide_suggestions(
            problem_area=problem_area,
            goals=goals,
            context_info=context_info,
            user_context=user_context
        )
        
        print(f"\n🤖 Smart Advisor:\n{response}")
        
        # Save the session to chat history
        conversation_id = str(uuid.uuid4())
        chat_entry = ChatHistory(
            user_id=self.current_user.id,
            conversation_id=conversation_id
        )
        goals_str = f" | Goals: {goals}" if goals else ""
        context_str = f" | Context: {context_info}" if context_info else ""
        chat_entry.user_message = f"[SUGGESTIONS] Problem: {problem_area}{goals_str}{context_str}"
        chat_entry.bot_response = response
        
        self.session.add(chat_entry)
        self.session.commit()
        
        input("\nPress Enter to continue...")

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