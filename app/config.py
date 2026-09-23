import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'instance', 'research_mind.db'))
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