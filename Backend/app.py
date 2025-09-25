import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Post model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# Signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data['username']
    password = generate_password_hash(data['password'])

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists!"}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully!"}), 201

# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid username or password!"}), 401

    return jsonify({"message": "Login successful!"}), 200

# Upload drawing
@app.route('/upload', methods=['POST'])
def upload():
    username = request.form['username']
    file = request.files['file']

    if not file:
        return jsonify({"message": "No file provided"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    new_post = Post(username=username, filename=filename)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Upload successful!"}), 201

# Feed (return list of drawings)
@app.route('/feed', methods=['GET'])
def feed():
    posts = Post.query.all()
    return jsonify([{"username": p.username, "filename": p.filename} for p in posts])

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
