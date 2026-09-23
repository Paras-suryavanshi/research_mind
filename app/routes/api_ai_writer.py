from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import AIWriterDocument
from app.services.groq_service import GroqService

ai_writer_bp = Blueprint('ai_writer', __name__)

@ai_writer_bp.route('/tools', methods=['POST'])
@login_required
def handle_writer_tools():
    data = request.get_json(silent=True) or {}
    action = str(data.get('action', '')).strip().lower()
    text = str(data.get('text', '')).strip()
    prompts = {
        'improve': 'Improve the grammar, clarity, and academic tone of the text.',
        'rewrite': 'Rewrite the text for clarity and academic tone.',
        'expand': 'Expand the text with useful detail while preserving its factual meaning.',
        'shorten': 'Shorten the text while preserving its essential meaning.',
        'paraphrase': 'Paraphrase the text while preserving its meaning and factual details.',
        'cite': 'Suggest citation placeholders for claims in the text. Do not invent sources.',
        'explain': 'Explain the text clearly for an academic reader without adding unsupported claims.',
    }
    if action not in prompts:
        return jsonify({"error": "Unsupported AI writer action"}), 400
    if not text:
        return jsonify({"error": "Text is required"}), 400
    if len(text) > 12000:
        return jsonify({"error": "Text is too long"}), 400

    result = GroqService.generate_research_content(
        prompt=f"{prompts[action]}\n\nText:\n{text}",
        system_prompt="You are an academic writing assistant. Return only the requested revised text.",
    )
    if result["error"]:
        return jsonify({"error": result["error"]}), 502
    return jsonify({"data": result["content"], "action": action}), 200

@ai_writer_bp.route('/documents', methods=['GET', 'POST'])
@login_required
def documents():
    if request.method == 'GET':
        items = AIWriterDocument.query.filter_by(user_id=current_user.id).order_by(
            AIWriterDocument.updated_at.desc()
        ).all()
        return jsonify({"items": [{
            "id": item.id, "title": item.title, "content": item.content or "",
            "updated_at": item.updated_at.isoformat()
        } for item in items]}), 200
    data = request.get_json(silent=True) or {}
    title = str(data.get('title', 'Untitled Document')).strip()[:200] or 'Untitled Document'
    content = str(data.get('content', ''))
    document_id = data.get('id')
    document = None
    if document_id:
        try:
            document = AIWriterDocument.query.filter_by(
                id=int(document_id), user_id=current_user.id
            ).first()
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid document id"}), 400
        if not document:
            return jsonify({"error": "Document not found"}), 404
        document.title, document.content = title, content
    else:
        document = AIWriterDocument(user_id=current_user.id, title=title, content=content)
        db.session.add(document)
    db.session.commit()
    return jsonify({"message": "Document saved", "id": document.id}), 200