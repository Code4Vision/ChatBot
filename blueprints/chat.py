"""
Chat blueprint with local LLM integration and memory functionality
"""
import uuid
import json
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

from app import db
from models import ChatHistory, UserPreferences

# Local LLM integration
try:
    from gpt4all import GPT4All
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: GPT4All not available. Using mock responses.")

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

class ChatForm(FlaskForm):
    """Form for chat input with CSRF protection"""
    message = TextAreaField('Message', 
                           validators=[DataRequired(), Length(min=1, max=1000)],
                           render_kw={"placeholder": "Type your message here...", "rows": 3})
    submit = SubmitField('Send')

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
            # Initialize GPT4All with a lightweight model
            # You can download different models: mistral-7b-openorca.Q4_0.gguf, orca-mini-3b.gguf, etc.
            self.model = GPT4All("orca-mini-3b-gguf2.Q4_0.gguf")  # type: ignore
            self.model_loaded = True
            print("Local LLM model loaded successfully!")
            return True
        except Exception as e:
            print(f"Failed to load LLM model: {e}")
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
            
            context_parts.append(f"You are a helpful AI assistant chatting with {name}.")
            context_parts.append(f"Your response style should be: {style}.")
            
            if interests:
                context_parts.append(f"{name} is interested in: {', '.join(interests)}.")
        
        if conversation_history and len(conversation_history) > 0:
            context_parts.append("\nRecent conversation:")
            for entry in conversation_history[-3:]:  # Last 3 exchanges for context
                context_parts.append(f"User: {entry.user_message}")
                context_parts.append(f"Assistant: {entry.bot_response}")
        
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

# Initialize the chatbot engine
chatbot = ChatbotEngine()

@chat_bp.route("/")
@login_required
def chat_interface():
    """Main chat interface"""
    form = ChatForm()
    
    # Get recent chat history
    recent_history = ChatHistory.get_user_history(current_user.id, limit=20)
    recent_history.reverse()  # Show oldest first
    
    return render_template('chat.html', form=form, chat_history=recent_history)

@chat_bp.route("/send", methods=['POST'])
@login_required
def send_message():
    """Handle chat message sending"""
    form = ChatForm()
    
    if form.validate_on_submit():
        user_message = str(form.message.data).strip()
        
        # Get user preferences for personalization
        user_prefs = current_user.preferences
        user_context = user_prefs.preferences_data if user_prefs else {}
        
        # Get recent conversation history for context
        recent_history = ChatHistory.get_user_history(current_user.id, limit=5)
        
        # Generate bot response
        bot_response = chatbot.generate_response(
            user_message, 
            user_context=user_context,
            conversation_history=recent_history
        )
        
        # Save to database with encryption
        conversation_id = str(uuid.uuid4())
        chat_entry = ChatHistory()  # type: ignore
        chat_entry.user_id = current_user.id
        chat_entry.conversation_id = conversation_id
        chat_entry.user_message = user_message
        chat_entry.bot_response = bot_response
        
        db.session.add(chat_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user_message': user_message,
            'bot_response': bot_response,
            'timestamp': chat_entry.timestamp.strftime('%H:%M')
        })
    
    return jsonify({'success': False, 'errors': form.errors})

@chat_bp.route("/history")
@login_required
def chat_history():
    """View chat history page with strict user isolation"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Strict user isolation - only show current user's history
    history = ChatHistory.query.filter_by(user_id=current_user.id)\
                              .order_by(ChatHistory.timestamp.desc())\
                              .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('chat_history.html', history=history)

@chat_bp.route("/clear_history", methods=['POST'])
@login_required
def clear_history():
    """Clear user's chat history with strict user isolation"""
    # Ensure only current user's history is deleted
    deleted_count = ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash(f"Chat history cleared successfully! ({deleted_count} messages deleted)", "info")
    return redirect(url_for('chat.chat_interface'))

@chat_bp.route("/export_history")
@login_required
def export_history():
    """Export chat history as JSON with strict user isolation"""
    # Strict user isolation - only export current user's history
    history = ChatHistory.get_user_history(current_user.id, limit=1000)
    
    export_data = {
        'user': current_user.username,
        'export_date': datetime.utcnow().isoformat(),
        'chat_history': [
            {
                'timestamp': entry.timestamp.isoformat(),
                'user_message': entry.user_message,
                'bot_response': entry.bot_response
            }
            for entry in reversed(history)  # Chronological order
        ]
    }
    
    response = jsonify(export_data)
    response.headers['Content-Disposition'] = f'attachment; filename=chat_history_{current_user.username}_{datetime.utcnow().strftime("%Y%m%d")}.json'
    return response