import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

def get_database_uri():
    """Use the local SQLite database by default and Render's URL in production."""
    app_env = os.environ.get('APP_ENV', 'development').strip().lower()
    local_database = 'sqlite:///' + os.path.join(basedir, 'instance', 'research_mind.db')
    database_url = os.environ.get('DATABASE_URL', '').strip()

    if app_env != 'production' and not database_url:
        return local_database

    if not database_url:
        raise RuntimeError('DATABASE_URL must be configured when APP_ENV=production.')

    # Normalize hosting-provider PostgreSQL schemes for Psycopg 3.
    if database_url.startswith('postgres://'):
        database_url = 'postgresql://' + database_url[len('postgres://'):]
    if database_url.startswith('postgresql://'):
        database_url = 'postgresql+psycopg://' + database_url[len('postgresql://'):]
    return database_url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    
    # Database Configuration
    APP_ENV = os.environ.get('APP_ENV', 'development').strip().lower()
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Groq API Key Pool
    GROQ_API_KEYS = [
        os.environ.get('GROQ_API_KEY_1'),
        os.environ.get('GROQ_API_KEY_2'),
        os.environ.get('GROQ_API_KEY_3'),
        os.environ.get('GROQ_API_KEY_4'),
        os.environ.get('GROQ_API_KEY_5'),
    ]
    
    # Filter out None/empty values to ensure valid key rotation
    GROQ_API_KEYS = [key for key in GROQ_API_KEYS if key and key.strip()]