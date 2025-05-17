from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from flask_login import UserMixin
from enum import Enum as PyEnum
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class PriorityLevel(PyEnum):
    High = 'High'
    Medium = 'Medium'
    Low = 'Low'

class TaskStatus(PyEnum):
    Pending = 'Pending'
    In_Progress = 'In Progress'
    Done = 'Done'



class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    priority = db.Column(Enum(PriorityLevel), nullable=False)
    status = db.Column(Enum(TaskStatus), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True, index=True)  # Link to Project
    # project = db.relationship('Project', backref='tasks')  # Relationship with Project

    def __repr__(self):
        return f"<Task {self.title}>"
    
        
    @staticmethod
    def get_active_tasks():
        return Task.query.filter(Task.deleted_at.is_(None))

    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    tasks = db.relationship('Task', backref='user', lazy='select')
    # projects = db.relationship('Project', backref='owner', lazy='dynamic')  # Relationship with Project

    def __repr__(self):
        return f"<User {self.username}>"
    
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # Project owner
    owner = db.relationship('User', backref='projects')  # Link to the User model
    tasks = db.relationship('Task', backref='project', lazy='select')  # Link to the Task model

    def __repr__(self):
        return f"<Project {self.name}>"