from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def get_profile():
    if request.method == 'PUT':
        data = request.get_json(silent=True) or {}
        username = str(data.get('username', '')).strip()
        email = str(data.get('email', '')).strip().lower()
        if not username or not email:
            return jsonify({"error": "Username and email are required"}), 400
        if len(username) > 20 or len(email) > 120:
            return jsonify({"error": "Username or email is too long"}), 400
        duplicate = User.query.filter(
            User.id != current_user.id,
            (User.username == username) | (User.email == email)
        ).first()
        if duplicate:
            return jsonify({"error": "Username or email already exists"}), 409
        current_user.username = username
        current_user.email = email
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"error": "Unable to save profile changes"}), 500
        return jsonify({"message": "Profile updated successfully"}), 200

    return jsonify({
        "username": current_user.username,
        "email": current_user.email,
        "joined": current_user.created_at.strftime('%Y-%m-%d')
    }), 200