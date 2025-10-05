import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

# Config for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ammar2003%40a@127.0.0.1:5432/palette_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    interests = db.Column(db.String(200), nullable=True)

class Friends(db.Model):
    __tablename__ = "friends"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"))

class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    __tablename__ = "likes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# Helper: Format timestamp
def format_timestamp(ts):
    now = datetime.utcnow()
    delta = now - ts
    if delta < timedelta(hours=1):
        return f"{int(delta.seconds / 60)}m ago"
    elif delta < timedelta(days=1):
        return f"{delta.seconds // 3600}h ago"
    else:
        return ts.strftime("%Y-%m-%d")

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

    return jsonify({"message": "Login successful!", "user_id": user.id}), 200

# Upload drawing with AI validation
@app.route('/upload', methods=['POST'])
def upload():
    user_id = request.form['user_id']
    file = request.files['file']

    if not file:
        return jsonify({"message": "No file provided"}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)
    if not is_sketch(temp_path):
        os.remove(temp_path)
        return jsonify({"message": "Invalid image: Must be a sketch or drawing."}), 400

    new_post = Post(user_id=user_id, filename=filename)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Upload successful!", "filename": filename}), 201

# AI Validation Function
def is_sketch(image_path, color_threshold=2000, edge_ratio_threshold=0.0010, entropy_threshold=10.0):
    img = cv2.imread(image_path)
    if img is None:
        print("Rejected: Invalid image file")
        return False

    # Color check (relaxed for colored sketches)
    unique_colors = len(np.unique(img.reshape(-1, 3), axis=0))
    if unique_colors > color_threshold:
        print(f"Rejected: Too many colors ({unique_colors})")
        return False

    # Grayscale and improved edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)  # Reduce noise for better detection
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    edges = cv2.Canny(thresh, 30, 100)  # Lower thresholds to detect faint/soft lines
    edge_ratio = np.sum(edges > 0) / (img.shape[0] * img.shape[1])
    if edge_ratio < edge_ratio_threshold:
        print(f"Rejected: Low edge ratio ({edge_ratio})")
        return False

    # Entropy check (sketches have lower complexity/entropy than photos)
    # Normalized entropy approximation
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_norm = hist / hist.sum()
    entropy = -np.sum(hist_norm * np.log2(hist_norm + np.finfo(float).eps))  # Avoid log(0)
    if entropy > entropy_threshold:
        print(f"Rejected: High entropy ({entropy})")
        return False

    print(f"Accepted: Colors ({unique_colors}), Edges ({edge_ratio}), Entropy ({entropy})")
    return True
   
@app.route('/feed', methods=['GET'])
def feed():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    feed_data = []
    for p in posts:
        likes = Like.query.filter_by(post_id=p.id).count()
        comments = Comment.query.filter_by(post_id=p.id).all()
        user = User.query.get(p.user_id)
        feed_data.append({
            "id": p.id,
            "user_id": p.user_id,
            "username": user.username,
            "profile_pic": user.profile_pic,
            "filename": p.filename,
            "timestamp": format_timestamp(p.timestamp),
            "likes_count": likes,
            "comments": [{"id": c.id, "user_id": c.user_id, "username": User.query.get(c.user_id).username, "text": c.text, "timestamp": format_timestamp(c.timestamp)} for c in comments]
        })
    return jsonify(feed_data)


# Like/Unlike
@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user_id = request.json['user_id']
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    if existing_like:
        db.session.delete(existing_like)
        action = "unliked"
    else:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        action = "liked"
    db.session.commit()
    likes_count = Like.query.filter_by(post_id=post_id).count()
    return jsonify({"action": action, "likes_count": likes_count}), 200

# Add Comment
@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    data = request.json
    user_id = data['user_id']
    text = data['text']
    if len(text.strip()) < 1:
        return jsonify({"message": "Comment too short"}), 400
    new_comment = Comment(user_id=user_id, post_id=post_id, text=text)
    db.session.add(new_comment)
    db.session.commit()
    user = User.query.get(user_id)
    return jsonify({
        "id": new_comment.id,
        "username": user.username,
        "text": text,
        "timestamp": format_timestamp(new_comment.timestamp)
    }), 201

# You Might Like (simple random posts, limit 5)
@app.route('/recommendations/<int:user_id>', methods=['GET'])
def recommendations(user_id):
    all_posts = Post.query.all()
    # Simple logic: Random 5 posts not by the user
    import random
    random_posts = random.sample([p for p in all_posts if p.user_id != user_id], min(5, len([p for p in all_posts if p.user_id != user_id])))
    rec_data = []
    for p in random_posts:
        user = User.query.get(p.user_id)
        rec_data.append({
            "id": p.id,
            "username": user.username,
            "filename": p.filename,
            "timestamp": format_timestamp(p.timestamp)
        })
    return jsonify(rec_data)

# Delete post
@app.route('/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    user_id = request.json['user_id']
    post = Post.query.get(post_id)
    if not post or post.user_id != user_id:
        return jsonify({"message": "Post not found or not authorized"}), 404

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], post.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully!"}), 200

# Upload profile picture
@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    user_id = request.form['user_id']
    file = request.files['file']

    if not file:
        return jsonify({"message": "No file provided"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.profile_pic = filename
    db.session.commit()

    return jsonify({"message": "Profile picture uploaded!", "filename": filename}), 201

# Get user profile
@app.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({
        "username": user.username,
        "profile_pic": user.profile_pic or None,
        "bio": user.bio or "",
        "location": user.location or "",
        "interests": user.interests or ""
    })

# Update profile
@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = request.json['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.bio = request.json.get('bio', user.bio)
    user.location = request.json.get('location', user.location)
    user.interests = request.json.get('interests', user.interests)
    db.session.commit()
    return jsonify({"message": "Profile updated!"}), 200

# Add friend
@app.route('/add_friend', methods=['POST'])
def add_friend():
    data = request.json
    user_id = data['user_id']
    friend_username = data['friend_username']

    friend = User.query.filter_by(username=friend_username).first()
    if not friend or friend.id == user_id:
        return jsonify({"message": "Invalid friend or self-add"}), 400

    if Friends.query.filter_by(user_id=user_id, friend_id=friend.id).first():
        return jsonify({"message": "Already friends"}), 400

    new_friend = Friends(user_id=user_id, friend_id=friend.id)
    db.session.add(new_friend)
    db.session.commit()
    return jsonify({"message": "Friend added!"}), 201

# Get friends
@app.route('/friends/<int:user_id>', methods=['GET'])
def get_friends(user_id):
    friends = Friends.query.filter_by(user_id=user_id).all()
    friend_ids = [f.friend_id for f in friends]
    friend_users = User.query.filter(User.id.in_(friend_ids)).all()
    return jsonify([{"username": u.username} for u in friend_users])

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)