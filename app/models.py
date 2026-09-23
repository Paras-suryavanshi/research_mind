from datetime import datetime, timezone
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    projects = db.relationship('Project', backref='owner', lazy=True, cascade="all, delete-orphan")
    searches = db.relationship('SearchHistory', backref='user', lazy=True, cascade="all, delete-orphan")
    library_items = db.relationship('LibraryItem', backref='user', lazy=True, cascade="all, delete-orphan")
    documents = db.relationship('AIWriterDocument', backref='author', lazy=True, cascade="all, delete-orphan")
    chats = db.relationship('ChatHistory', backref='user', lazy=True, cascade="all, delete-orphan")

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    searches = db.relationship('SearchHistory', backref='project', lazy=True)
    library_items = db.relationship('LibraryItem', backref='project', lazy=True)
    documents = db.relationship('AIWriterDocument', backref='project', lazy=True)
    systematic_reviews = db.relationship('SystematicReview', backref='project', lazy=True)

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    query = db.Column(db.Text, nullable=False)
    research_mode = db.Column(db.String(50), nullable=False) # e.g., 'quick_qa', 'literature_review'
    selected_source = db.Column(db.String(50), nullable=False) # 'arxiv', 'pubmed', 'crossref', 'core'
    result_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    pdf_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ChatConversation(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    pdf_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade="all, delete-orphan")

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('chat_conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class LibraryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    authors = db.Column(db.String(500), nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    source_platform = db.Column(db.String(50), nullable=False)
    doi = db.Column(db.String(100), nullable=True)
    publication_date = db.Column(db.String(50), nullable=True)
    pdf_url = db.Column(db.String(500), nullable=True)
    saved_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class AIWriterDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False, default="Untitled Document")
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SystematicReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    research_question = db.Column(db.Text, nullable=False)
    inclusion_criteria = db.Column(db.Text, nullable=True)
    exclusion_criteria = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Setup") # Setup, Searching, Screening, Extraction, Completed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ReviewPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('systematic_review.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    authors = db.Column(db.String(500), nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))