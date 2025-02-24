# app/__init__.py
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLA()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Basic config
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    AppBuilder(app, db.session)
    socketio.init_app(app)
    
    with app.app_context():
        from . import views, models
        db.create_all()
    
    return app

# app/models.py
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class Node(Model):
    __tablename__ = 'node'
    
    id = Column(Integer, primary_key=True)
    content = Column(String(1000), nullable=False)
    parent_id = Column(Integer, ForeignKey('node.id'), nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    children = relationship('Node', backref='parent', remote_side=[id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'parent_id': self.parent_id,
            'is_completed': self.is_completed,
            'children': [child.to_dict() for child in self.children]
        }

# app/views.py
from flask import render_template, request, jsonify
from flask_appbuilder import ModelView, BaseView, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_socketio import emit
from . import db, socketio
from .models import Node

class NodeModelView(ModelView):
    datamodel = SQLAInterface(Node)
    list_columns = ['content', 'is_completed', 'created_at']
    show_columns = ['content', 'is_completed', 'created_at', 'updated_at']
    edit_columns = ['content', 'is_completed']
    add_columns = ['content', 'parent_id']

class WorkflowyView(BaseView):
    default_view = 'workflowy'
    
    @expose('/')
    def workflowy(self):
        root_nodes = db.session.query(Node).filter(Node.parent_id == None).all()
        return render_template(
            'workflowy.html',
            nodes=[node.to_dict() for node in root_nodes]
        )
    
    @expose('/api/nodes', methods=['POST'])
    def create_node(self):
        data = request.json
        new_node = Node(
            content=data['content'],
            parent_id=data.get('parent_id')
        )
        db.session.add(new_node)
        db.session.commit()
        
        socketio.emit('node_created', new_node.to_dict())
        return jsonify(new_node.to_dict())
    
    @expose('/api/nodes/<int:node_id>', methods=['PUT'])
    def update_node(self, node_id):
        node = db.session.query(Node).get(node_id)
        data = request.json
        
        if 'content' in data:
            node.content = data['content']
        if 'is_completed' in data:
            node.is_completed = data['is_completed']
        if 'parent_id' in data:
            node.parent_id = data['parent_id']
            
        db.session.commit()
        socketio.emit('node_updated', node.to_dict())
        return jsonify(node.to_dict())
    
    @expose('/api/nodes/<int:node_id>', methods=['DELETE'])
    def delete_node(self, node_id):
        node = db.session.query(Node).get(node_id)
        db.session.delete(node)
        db.session.commit()
        socketio.emit('node_deleted', {'id': node_id})
        return jsonify({'success': True})

# app/templates/workflowy.html
{% extends "appbuilder/base.html" %}

{% block content %}
<div class="container-fluid">
    <div id="workflowy-app" class="row">
        <div class="col-md-12">
            <div id="nodes-container"></div>
            <button id="add-root-node" class="btn btn-primary">Add Root Node</button>
        </div>
    </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<script>
const socket = io();
let currentNodes = {{ nodes | tojson | safe }};

function renderNode(node, level = 0) {
    const div = document.createElement('div');
    div.classList.add('node');
    div.style.marginLeft = `${level * 20}px`;
    
    const content = document.createElement('div');
    content.classList.add('node-content');
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = node.is_completed;
    checkbox.onclick = () => updateNode(node.id, { is_completed: checkbox.checked });
    
    const text = document.createElement('span');
    text.contentEditable = true;
    text.textContent = node.content;
    text.onblur = () => updateNode(node.id, { content: text.textContent });
    
    const controls = document.createElement('div');
    controls.classList.add('node-controls');
    
    const addButton = document.createElement('button');
    addButton.textContent = '+';
    addButton.onclick = () => createNode('New node', node.id);
    
    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'x';
    deleteButton.onclick = () => deleteNode(node.id);
    
    content.appendChild(checkbox);
    content.appendChild(text);
    controls.appendChild(addButton);
    controls.appendChild(deleteButton);
    div.appendChild(content);
    div.appendChild(controls);
    
    if (node.children && node.children.length > 0) {
        const childrenDiv = document.createElement('div');
        childrenDiv.classList.add('children');
        node.children.forEach(child => {
            childrenDiv.appendChild(renderNode(child, level + 1));
        });
        div.appendChild(childrenDiv);
    }
    
    return div;
}

function renderNodes() {
    const container = document.getElementById('nodes-container');
    container.innerHTML = '';
    currentNodes.forEach(node => {
        container.appendChild(renderNode(node));
    });
}

async function createNode(content, parentId = null) {
    const response = await fetch('/workflowy/api/nodes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, parent_id: parentId })
    });
    const newNode = await response.json();
    if (!parentId) {
        currentNodes.push(newNode);
    }
    renderNodes();
}

async function updateNode(nodeId, updates) {
    const response = await fetch(`/workflowy/api/nodes/${nodeId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    });
    const updatedNode = await response.json();
    renderNodes();
}

async function deleteNode(nodeId) {
    await fetch(`/workflowy/api/nodes/${nodeId}`, {
        method: 'DELETE'
    });
    currentNodes = currentNodes.filter(node => node.id !== nodeId);
    renderNodes();
}

document.getElementById('add-root-node').onclick = () => {
    createNode('New root node');
};

// Socket.io event handlers
socket.on('node_created', (node) => {
    if (!node.parent_id) {
        currentNodes.push(node);
        renderNodes();
    }
});

socket.on('node_updated', (node) => {
    renderNodes();
});

socket.on('node_deleted', (data) => {
    currentNodes = currentNodes.filter(node => node.id !== data.id);
    renderNodes();
});

// Initial render
renderNodes();
</script>

<style>
.node {
    margin: 5px 0;
}

.node-content {
    display: flex;
    align-items: center;
    gap: 10px;
}

.node-controls {
    display: inline-flex;
    gap: 5px;
    margin-left: 10px;
}

.node-controls button {
    padding: 2px 6px;
    border: 1px solid #ccc;
    border-radius: 3px;
    background: #fff;
    cursor: pointer;
}

[contenteditable] {
    padding: 2px 5px;
    border: 1px solid transparent;
}

[contenteditable]:focus {
    border-color: #ccc;
    outline: none;
}
</style>

{% endblock %}

# config.py
import os
from flask_appbuilder.security.manager import (
    AUTH_OID,
    AUTH_REMOTE_USER,
    AUTH_DB,
    AUTH_LDAP,
    AUTH_OAUTH,
)

basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = "your-secret-key-here"

# Database
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-AppBuilder configuration
AUTH_TYPE = AUTH_DB
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public"

# App name
APP_NAME = "Workflowy Clone"

# App theme
APP_THEME = "cosmo"

# run.py
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)
