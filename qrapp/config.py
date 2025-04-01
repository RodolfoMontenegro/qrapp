import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "supersecretkey"  # Change this to a secure key
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    CHROMA_DB_DIR = "chromadb_data"
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'geopdf'}

    # Flask-SQLAlchemy Configuration (Fixing the missing database URI)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'flask_session.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
# Crear el directorio de subida si no existe
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
