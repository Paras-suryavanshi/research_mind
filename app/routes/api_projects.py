from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Project

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
@login_required
def get_projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    project_list = [{"id": p.id, "name": p.name, "description": p.description} for p in projects]
    return jsonify({"projects": project_list}), 200

@projects_bp.route('/', methods=['POST'])
@login_required
def create_project():
    data = request.get_json(silent=True)
    name = str(data.get('name', '')).strip() if data else ''
    if not name:
        return jsonify({"error": "Project name is required"}), 400
    if len(name) > 100:
        return jsonify({"error": "Project name is too long"}), 400
        
    new_project = Project(
        name=name,
        description=str(data.get('description', '')).strip()[:10000],
        user_id=current_user.id
    )
    
    try:
        db.session.add(new_project)
        db.session.commit()
        return jsonify({"message": "Project created", "project_id": new_project.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create project"}), 500

@projects_bp.route('/<int:project_id>', methods=['PUT', 'DELETE'])
@login_required
def update_or_delete_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404
    if request.method == 'DELETE':
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "Project deleted"}), 200
    data = request.get_json(silent=True) or {}
    if 'name' in data:
        name = str(data['name']).strip()
        if not name or len(name) > 100:
            return jsonify({"error": "Project name is invalid"}), 400
        project.name = name
    if 'description' in data:
        project.description = str(data['description']).strip()[:10000]
    db.session.commit()
    return jsonify({"message": "Project updated", "project": {
        "id": project.id, "name": project.name, "description": project.description
    }}), 200