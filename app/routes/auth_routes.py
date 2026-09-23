from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import db, bcrypt
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    if current_user.is_authenticated:
        return jsonify({"error": "User already logged in"}), 400

    data = request.get_json(silent=True)
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing required fields"}), 400

    username = str(data['username']).strip()
    email = str(data['email']).strip().lower()
    password = str(data['password'])
    if not username or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
    if len(username) > 20 or len(email) > 120:
        return jsonify({"error": "Username or email is too long"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password_hash=hashed_password)
    
    try:
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify({"message": "Account created successfully", "user_id": user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred during registration"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({"message": "Already logged in"}), 200

    data = request.get_json(silent=True)
    if not data or not data.get('identifier') or not data.get('password'):
        return jsonify({"error": "Missing login credentials"}), 400

    identifier = str(data['identifier']).strip()
    user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        login_user(user, remember=data.get('remember', False))
        return jsonify({"message": "Logged in successfully", "user_id": user.id}), 200
    
    return jsonify({"error": "Invalid username/email or password"}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200