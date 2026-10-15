import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'tianshu-dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tianshu.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.moonshot.cn')
    LLM_MODEL = os.getenv('LLM_MODEL', 'kimi-k2.6')
