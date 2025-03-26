from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship

# Association table for user-permission many-to-many relationship
user_permissions = db.Table('user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('command_permission.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    logs = db.relationship('SystemCallLog', backref='user', lazy='dynamic')
    permissions = db.relationship('CommandPermission', secondary=user_permissions, 
                                  backref=db.backref('users', lazy='dynamic'))
    
    def __repr__(self):
        return f'<User {self.username}>'

class CommandPermission(db.Model):
    __tablename__ = 'command_permission'
    
    id = db.Column(db.Integer, primary_key=True)
    command_pattern = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.command_pattern}>'

class SystemCallLog(db.Model):
    __tablename__ = 'system_call_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    command = db.Column(db.String(255), nullable=False)
    output = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    exit_code = db.Column(db.Integer, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)  # in seconds
    ip_address = db.Column(db.String(45), nullable=True)
    
    def __repr__(self):
        return f'<SystemCallLog {self.command}>'
