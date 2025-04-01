import qrcode
import os
import uuid
from io import BytesIO
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from PIL import Image
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database.chroma_db import chroma_db
from auth.models import db, User
from auth.auth_routes import auth

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# For decryption
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth)

db.init_app(app)
with app.app_context():
    db.create_all()

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

def create_default_admin():
    """Manually create a default admin user if one doesn't exist."""
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        encryption_key = os.getenv("ENCRYPTION_KEY")
        encrypted_password = os.getenv("DEFAULT_ADMIN_PASSWORD_ENC")
        if not encryption_key or not encrypted_password:
            raise Exception("Missing ENCRYPTION_KEY or DEFAULT_ADMIN_PASSWORD_ENC in .env file!")
        fernet = Fernet(encryption_key)
        default_admin_password = fernet.decrypt(encrypted_password.encode()).decode()
        hashed_password = generate_password_hash(default_admin_password, method='pbkdf2:sha256')
        admin_user = User(username='admin', password=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created: username='admin'")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# In-memory dict: token -> file_id
# For real usage, store tokens in a database or table for persistence
token_map = {}

@app.route('/')
@login_required
def index():
    files = chroma_db.get_all_files()
    return render_template('index.html', files=files)

@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin:
        return "You do not have admin privileges.", 403
    users = User.query.all()
    return render_template("dashboard.html", users=users)

@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form.get('text')
    if not text:
        return "Text content required", 400

    metadata = {"type": "document", "filename": "text_entry"}
    doc_id = chroma_db.add_text_document(text, metadata)
    return jsonify({"message": "Text stored successfully", "document_id": doc_id})

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)

    try:
        file.save(filepath)
        with Image.open(filepath) as img:
            img.verify()
    except Exception as e:
        os.remove(filepath)
        return jsonify({"error": "Invalid image file", "details": str(e)}), 400

    relative_path = os.path.relpath(filepath, os.getcwd())
    metadata = {
        "type": "image",
        "filename": filename,
        "path": relative_path,
        "description": filename  # Para que se pueda buscar como texto también
    }

    # Guarda tanto el texto como la imagen
    img_id = chroma_db.add_image_with_text(filepath, description=filename, metadata=metadata)
    return jsonify({"message": "Image stored successfully", "image_id": img_id})

@app.route('/search_text', methods=['GET'])
def search_text():
    query = request.args.get('q')
    if not query:
        return "Query text required", 400
    results = chroma_db.search_by_text(query)
    return jsonify(results)

@app.route('/search_image', methods=['POST'])
def search_image():
    if 'file' not in request.files:
        return "No file provided", 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    results = chroma_db.search_by_image(filepath)
    return jsonify(results)

@app.route('/generate_qr/<file_id>')
def generate_qr(file_id):
    file_metadata = chroma_db.get_file_metadata(file_id)
    if not file_metadata or "path" not in file_metadata:
        return "File not found", 404

    token = str(uuid.uuid4())
    token_map[token] = file_id
    file_url = url_for('access_via_token', token=token, _external=True)

    qr = qrcode.make(file_url)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/access/<token>')
def access_via_token(token):
    if token not in token_map:
        return "Invalid or expired token", 404

    file_id = token_map[token]
    file_metadata = chroma_db.get_file_metadata(file_id)
    if not file_metadata or "path" not in file_metadata:
        return "File not found", 404

    full_path = os.path.join(os.getcwd(), file_metadata["path"])
    if not os.path.exists(full_path):
        return "File not found on disk", 404

    return send_file(full_path)

@app.route('/view_file/<string:file_id>')
def view_file(file_id):
    file_metadata = chroma_db.get_file_metadata(file_id)
    if not file_metadata or "path" not in file_metadata:
        return "File not found", 404

    full_path = os.path.join(os.getcwd(), file_metadata["path"])
    if not os.path.exists(full_path):
        return "File not found on disk", 404

    return send_file(full_path)

@app.route('/download_file/<string:file_id>')
def download_file(file_id):
    file_metadata = chroma_db.get_file_metadata(file_id)
    full_path = os.path.join(os.getcwd(), file_metadata["path"])
    return send_file(full_path, as_attachment=True)

@app.route('/delete_file/<file_id>', methods=['POST'])
def delete_file(file_id):
    try:
        chroma_db.delete_file(file_id)
        return jsonify({"message": "File deleted successfully", "file_id": file_id})
    except Exception as e:
        return jsonify({"error": "Failed to delete file", "details": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        create_default_admin()
    app.run(debug=True, host='0.0.0.0', port=5001)
