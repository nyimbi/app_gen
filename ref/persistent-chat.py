# app/models.py
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class MessageType(enum.Enum):
    USER = "user"
    BOT = "bot"
    LLM = "llm"

class ChatMessage(Model):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    content = Column(String(1000))
    message_type = Column(Enum(MessageType))
    sender_id = Column(Integer, ForeignKey('ab_user.id'))
    recipient_id = Column(Integer, ForeignKey('ab_user.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sender = relationship('User', foreign_keys=[sender_id])
    recipient = relationship('User', foreign_keys=[recipient_id])

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'message_type': self.message_type.value,
            'sender': self.sender.username,
            'recipient': self.recipient.username if self.recipient else None,
            'created_at': self.created_at.isoformat()
        }

# app/chat.py
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from flask_socketio import emit
from . import db, socketio
from .models import ChatMessage, MessageType, User
import openai

chat_blueprint = Blueprint('chat', __name__)

# Initialize OpenAI (you'll need to set your API key in config)
openai.api_key = current_app.config.get('OPENAI_API_KEY')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {current_user.username}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {current_user.username}')

@socketio.on('message')
def handle_message(data):
    message_type = MessageType[data.get('type', 'USER').upper()]
    recipient_id = data.get('recipient_id')
    
    message = ChatMessage(
        content=data['content'],
        message_type=message_type,
        sender_id=current_user.id,
        recipient_id=recipient_id
    )
    db.session.add(message)
    db.session.commit()
    
    # Broadcast message to appropriate recipients
    if recipient_id:
        # Direct message
        emit('new_message', message.to_dict(), room=f'user_{recipient_id}')
        emit('new_message', message.to_dict(), room=f'user_{current_user.id}')
    else:
        # Global message
        emit('new_message', message.to_dict(), broadcast=True)

@chat_blueprint.route('/api/chat/history')
def get_chat_history():
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(50).all()
    return jsonify([msg.to_dict() for msg in messages])

@chat_blueprint.route('/api/chat/users')
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username
    } for user in users])

@chat_blueprint.route('/api/chat/bot', methods=['POST'])
def chat_with_bot():
    content = request.json.get('content')
    
    # Simple bot response logic - replace with your chatbot implementation
    response = f"Bot: I received your message: {content}"
    
    message = ChatMessage(
        content=response,
        message_type=MessageType.BOT,
        sender_id=None,
        recipient_id=current_user.id
    )
    db.session.add(message)
    db.session.commit()
    
    emit('new_message', message.to_dict(), room=f'user_{current_user.id}', namespace='/')
    return jsonify(message.to_dict())

@chat_blueprint.route('/api/chat/llm', methods=['POST'])
def generate_with_llm():
    content = request.json.get('content')
    
    try:
        # OpenAI API call
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=content,
            max_tokens=150
        )
        
        llm_response = response.choices[0].text.strip()
        
        message = ChatMessage(
            content=llm_response,
            message_type=MessageType.LLM,
            sender_id=None,
            recipient_id=current_user.id
        )
        db.session.add(message)
        db.session.commit()
        
        emit('new_message', message.to_dict(), room=f'user_{current_user.id}', namespace='/')
        return jsonify(message.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# app/templates/appbuilder/base.html
{% extends 'appbuilder/baselayout.html' %}

{% block content %}
    {{super()}}
    
    <!-- Chat Box -->
    <div id="chat-box" class="chat-box">
        <div class="chat-header">
            <span class="chat-title">Chat</span>
            <div class="chat-controls">
                <button id="minimize-chat" class="btn btn-sm btn-light">_</button>
                <button id="close-chat" class="btn btn-sm btn-light">×</button>
            </div>
        </div>
        
        <div class="chat-tabs">
            <button class="chat-tab active" data-tab="global">Global</button>
            <button class="chat-tab" data-tab="direct">Direct</button>
            <button class="chat-tab" data-tab="bot">Bot</button>
            <button class="chat-tab" data-tab="llm">LLM</button>
        </div>
        
        <div class="chat-content">
            <div id="messages" class="messages"></div>
            
            <div class="chat-input-area">
                <select id="recipient-select" class="form-control" style="display: none;">
                    <option value="">Select user...</option>
                </select>
                <div class="input-group">
                    <input type="text" id="message-input" class="form-control" placeholder="Type a message...">
                    <button id="send-message" class="btn btn-primary">Send</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Chat Styles -->
    <style>
        .chat-box {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            height: 400px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            z-index: 1000;
        }
        
        .chat-header {
            padding: 10px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 8px 8px 0 0;
        }
        
        .chat-controls {
            display: flex;
            gap: 5px;
        }
        
        .chat-tabs {
            display: flex;
            padding: 5px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
        }
        
        .chat-tab {
            padding: 5px 10px;
            border: none;
            background: none;
            cursor: pointer;
        }
        
        .chat-tab.active {
            background: #fff;
            border-radius: 4px;
        }
        
        .chat-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        
        .message {
            margin: 5px 0;
            padding: 8px;
            border-radius: 4px;
            max-width: 80%;
        }
        
        .message.sent {
            background: #007bff;
            color: white;
            margin-left: auto;
        }
        
        .message.received {
            background: #f1f1f1;
            margin-right: auto;
        }
        
        .chat-input-area {
            padding: 10px;
            border-top: 1px solid #ddd;
        }
        
        .minimized {
            height: 45px;
            overflow: hidden;
        }
    </style>

    <!-- Chat Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const socket = io();
            let currentTab = 'global';
            let users = [];
            
            // Connect to WebSocket
            socket.on('connect', () => {
                console.log('Connected to WebSocket');
                loadChatHistory();
                loadUsers();
            });
            
            // Handle new messages
            socket.on('new_message', (message) => {
                appendMessage(message);
            });
            
            // UI Elements
            const chatBox = document.getElementById('chat-box');
            const messagesDiv = document.getElementById('messages');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-message');
            const recipientSelect = document.getElementById('recipient-select');
            const minimizeButton = document.getElementById('minimize-chat');
            const closeButton = document.getElementById('close-chat');
            
            // Tab handling
            document.querySelectorAll('.chat-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    document.querySelectorAll('.chat-tab').forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    currentTab = tab.dataset.tab;
                    
                    // Show/hide recipient select based on tab
                    recipientSelect.style.display = currentTab === 'direct' ? 'block' : 'none';
                    
                    // Clear messages
                    messagesDiv.innerHTML = '';
                    loadChatHistory();
                });
            });
            
            // Minimize/Maximize
            minimizeButton.addEventListener('click', () => {
                chatBox.classList.toggle('minimized');
            });
            
            // Close
            closeButton.addEventListener('click', () => {
                chatBox.style.display = 'none';
            });
            
            // Send message
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
            
            function sendMessage() {
                const content = messageInput.value.trim();
                if (!content) return;
                
                const messageData = {
                    content: content,
                    type: currentTab.toUpperCase()
                };
                
                if (currentTab === 'direct') {
                    messageData.recipient_id = recipientSelect.value;
                }
                
                if (currentTab === 'bot') {
                    fetch('/api/chat/bot', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ content })
                    });
                } else if (currentTab === 'llm') {
                    fetch('/api/chat/llm', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ content })
                    });
                } else {
                    socket.emit('message', messageData);
                }
                
                messageInput.value = '';
            }
            
            async function loadChatHistory() {
                const response = await fetch('/api/chat/history');
                const messages = await response.json();
                
                messagesDiv.innerHTML = '';
                messages.reverse().forEach(message => {
                    appendMessage(message);
                });
            }
            
            async function loadUsers() {
                const response = await fetch('/api/chat/users');
                users = await response.json();
                
                recipientSelect.innerHTML = '<option value="">Select user...</option>';
                users.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = user.username;
                    recipientSelect.appendChild(option);
                });
            }
            
            function appendMessage(message) {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.classList.add(message.sender === currentUser ? 'sent' : 'received');
                
                const content = document.createElement('div');
                content.textContent = message.content;
                
                const meta = document.createElement('small');
                meta.textContent = `${message.sender} - ${new Date(message.created_at).toLocaleTimeString()}`;
                meta.style.opacity = '0.7';
                
                messageDiv.appendChild(content);
                messageDiv.appendChild(meta);
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        });
    </script>
{% endblock %}

# app/__init__.py update
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLA()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Load config
    app.config.from_object('config')
    
    # Initialize extensions
    db.init_app(app)
    AppBuilder(app, db.session)
    socketio.init_app(app)
    
    with app.app_context():
        # Register blueprints
        from .chat import chat_blueprint
        app.register_blueprint(chat_blueprint)
        
        # Create database tables
        from . import models
        db.create_all()
    
    return app

# config.py update
# Add these settings to your existing config.py

# Chat configuration
CHAT_MESSAGE_HISTORY = 50  # Number of messages to load in history
OPENAI_API_KEY = 'your-openai-api-key'  # Replace with your actual API key

# Additional requirements
# pip install flask-socketio openai