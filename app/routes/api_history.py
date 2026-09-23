from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import SearchHistory, ChatHistory, ChatConversation, ChatMessage

history_bp = Blueprint('history', __name__)

@history_bp.route('/searches', methods=['GET'])
@login_required
def get_search_history():
    searches = db.session.query(SearchHistory).filter_by(user_id=current_user.id).order_by(
        SearchHistory.created_at.desc()
    ).all()
    return jsonify({"items": [{
        "id": item.id,
        "query": item.query,
        "mode": item.research_mode,
        "source": item.selected_source,
        "summary": item.result_summary,
        "project_id": item.project_id,
        "created_at": item.created_at.isoformat(),
    } for item in searches]}), 200

@history_bp.route('/chats', methods=['GET'])
@login_required
def get_chat_history():
    conversations = db.session.query(ChatConversation).filter_by(user_id=current_user.id).order_by(
        ChatConversation.updated_at.desc()
    ).all()
    return jsonify({"items": [{
        "id": item.id, "title": item.title, "pdf_url": item.pdf_url,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "messages": [{
            "role": message.role, "content": message.content,
            "created_at": message.created_at.isoformat()
        } for message in item.messages]
    } for item in conversations]}), 200

@history_bp.route('/chats/<conversation_id>', methods=['GET'])
@login_required
def get_chat(conversation_id):
    conversation = ChatConversation.query.filter_by(
        id=conversation_id, user_id=current_user.id
    ).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify({
        "id": conversation.id, "title": conversation.title,
        "pdf_url": conversation.pdf_url,
        "messages": [{
            "role": message.role, "content": message.content,
            "created_at": message.created_at.isoformat()
        } for message in conversation.messages]
    }), 200
