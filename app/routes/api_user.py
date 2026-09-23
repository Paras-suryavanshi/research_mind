from flask import Blueprint, jsonify
from flask_login import login_required, current_user

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    return jsonify({
        "username": current_user.username,
        "email": current_user.email,
        "joined": current_user.created_at.strftime('%Y-%m-%d')
    }), 200