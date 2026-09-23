from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import LibraryItem
from app import db

library_bp = Blueprint('library', __name__)
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

@library_bp.route('/', methods=['GET'])
@login_required
def get_library_items():
    items = LibraryItem.query.filter_by(user_id=current_user.id).all()
    data = [{"id": i.id, "title": i.title, "authors": i.authors, "source": i.source_platform,
             "abstract": i.abstract, "pdf_url": i.pdf_url, "url": i.pdf_url,
             "publication_date": i.publication_date} for i in items]
    return jsonify({"items": data}), 200

@library_bp.route('/', methods=['POST'])
@login_required
def save_library_item():
    data = request.get_json(silent=True) or {}
    title = str(data.get('title', '')).strip()
    if not title:
        return jsonify({"error": "Paper title is required"}), 400
    item = LibraryItem(user_id=current_user.id, title=title,
        authors=str(data.get('authors', '')), abstract=str(data.get('abstract', '')),
        source_platform=str(data.get('source', data.get('source_platform', 'Unknown'))),
        doi=data.get('doi'), publication_date=data.get('publication_date'),
        pdf_url=data.get('pdf_url') or data.get('url'))
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Paper saved", "id": item.id}), 201


@library_bp.route('/documents', methods=['POST'])
@login_required
def upload_library_document():
    uploaded = request.files.get('file') or request.files.get('document')
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "A document file is required"}), 400
    if request.content_length and request.content_length > MAX_UPLOAD_BYTES:
        return jsonify({"error": "Document exceeds the 50MB limit"}), 413

    filename = uploaded.filename.rsplit('\\', 1)[-1].rsplit('/', 1)[-1].strip()
    extension = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    if extension not in {'pdf', 'txt', 'doc', 'docx', 'csv', 'xlsx', 'xls'}:
        return jsonify({"error": "Unsupported document type"}), 415
    content = uploaded.stream.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        return jsonify({"error": "Document exceeds the 50MB limit"}), 413

    item = LibraryItem(
        user_id=current_user.id,
        title=filename[:255],
        authors='',
        abstract=f'Uploaded document: {filename}',
        source_platform='Uploaded document',
        publication_date=datetime.now(timezone.utc).date().isoformat(),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Document added to library", "id": item.id, "filename": filename}), 201

@library_bp.route('/<int:item_id>', methods=['DELETE'])
@login_required
def delete_library_item(item_id):
    item = LibraryItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({"error": "Library item not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Paper removed"}), 200