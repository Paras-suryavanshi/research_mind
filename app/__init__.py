import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from app.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    # Resolve absolute path to the 'app' directory where templates and static folders reside
    app_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(app_dir, 'templates')
    static_dir = os.path.join(app_dir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if database_uri.startswith('sqlite:///'):
        database_path = database_uri.removeprefix('sqlite:///')
        os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth_routes import auth_bp
    from app.routes.page_routes import page_bp
    from app.routes.api_research import research_bp
    from app.routes.api_projects import projects_bp
    from app.routes.api_library import library_bp
    from app.routes.api_ai_writer import ai_writer_bp
    from app.routes.api_user import user_bp
    from app.routes.api_history import history_bp
    from app.routes.api_systematic import systematic_bp
    from app.routes.api_papers import papers_bp
    from app.routes.api_data_analysis import data_analysis_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(page_bp)
    app.register_blueprint(research_bp, url_prefix='/api/research')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(library_bp, url_prefix='/api/library')
    app.register_blueprint(ai_writer_bp, url_prefix='/api/ai_writer')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    app.register_blueprint(systematic_bp, url_prefix='/api/systematic')
    app.register_blueprint(papers_bp, url_prefix='/api/papers')
    app.register_blueprint(data_analysis_bp, url_prefix='/api/data-analysis')

    # Ensure a fresh deployment has the model tables before handling requests.
    with app.app_context():
        db.create_all()

    return app