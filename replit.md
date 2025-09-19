# Secure Flask Chatbot

## Overview

This is a production-ready Flask chatbot application with fully local authentication and mobile-first UI design. The system provides secure, personalized chat experiences with encrypted conversation storage, user preferences management, and comprehensive chat history tracking. The application uses GPT4All for offline AI responses, ensuring complete privacy with no external dependencies while maintaining intelligent conversation capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for mobile-first responsive UI
- **Security**: CSRF protection with Flask-WTF for all forms
- **User Interface**: Mobile-first design with touch-friendly controls, optimized chat interface, and PWA-like experience
- **Session Management**: Secure cookie handling with HTTP-only and secure flags
- **Mobile Optimization**: Large touch targets, sticky navigation, responsive typography, and gesture-friendly interface

### Backend Architecture
- **Framework**: Flask with application factory pattern for modular design
- **Authentication**: Local username/password authentication with secure password hashing (Werkzeug)
- **Authorization**: Flask-Login for session management and route protection
- **Database ORM**: SQLAlchemy with declarative base for type-safe database operations
- **Blueprint Structure**: Modular route organization separating auth, chat, and main functionality

### Data Storage Solutions
- **Database**: SQLAlchemy-compatible database (configured via DATABASE_URL environment variable)
- **Encryption**: Fernet symmetric encryption for sensitive chat data at rest
- **Models**: 
  - User model with local password authentication
  - ChatHistory model with encrypted message storage
  - UserPreferences model for personalization settings
- **Data Isolation**: User-specific data access with proper foreign key relationships

### Security Implementation
- **Data Encryption**: All chat messages encrypted before database storage using Fernet
- **Environment Variables**: Secure configuration management for secrets (SESSION_SECRET, ENCRYPTION_KEY)
- **CSRF Protection**: Comprehensive form protection against cross-site request forgery
- **Session Security**: Secure cookie configuration with appropriate flags and timeouts
- **Password Security**: Secure password hashing and validation with Werkzeug security functions

### AI Integration
- **Local LLM**: GPT4All integration for offline AI responses (orca-mini-3b model)
- **Fallback System**: Graceful degradation when LLM is unavailable
- **Memory System**: Conversation context preservation across chat sessions
- **Personalization**: User preference integration for response style and length customization

## External Dependencies

### No External Authentication Required
- **Local Authentication**: Self-contained username/password system with no external service dependencies
- **Complete Privacy**: All authentication handled locally without third-party services

### AI/ML Services
- **GPT4All**: Local language model library for offline AI responses
- **Model Files**: Requires downloading specific model files (orca-mini-3b-gguf2.Q4_0.gguf)

### Frontend Dependencies
- **Bootstrap 5**: CSS framework via CDN for responsive design
- **Font Awesome 6**: Icon library via CDN for UI elements
- **jQuery**: JavaScript library for dynamic frontend interactions

### Python Packages
- **Flask Ecosystem**: flask, flask-sqlalchemy, flask-login, flask-wtf
- **Security**: cryptography (Fernet encryption), werkzeug (password hashing)
- **Database**: SQLAlchemy ORM with connection pooling
- **HTTP Client**: requests library for external integrations

### Environment Configuration
- **Required Variables**: SESSION_SECRET, ENCRYPTION_KEY, DATABASE_URL
- **Optional Variables**: FLASK_ENV for development mode detection
- **Replit Integration**: REPLIT_DEV_DOMAIN for local development environment configuration