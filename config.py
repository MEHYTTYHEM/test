import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SECRET_KEYとGEMINI_API_KEYが.envファイルから読み込まれる
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')