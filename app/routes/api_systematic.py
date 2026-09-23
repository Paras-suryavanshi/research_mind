from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app import db
from app.models import ReviewPaper, SystematicReview

systematic_bp = Blueprint('systematic', __name__)

STEPS = ['Setup', 'Screening', 'Extraction', 'Analysis', 'Report']

def review_for_user(review_id):
    return SystematicReview.query.filter_by(id=review_id, user_id=current_user.id).first()

@systematic_bp.route('/reviews', methods=['GET', 'POST'])
@login_required
def reviews():
    if request.method == 'GET':
        items = SystematicReview.query.filter_by(user_id=current_user.id).order_by(
            SystematicReview.created_at.desc()
        ).all()
        return jsonify({'items': [{
            'id': item.id, 'research_question': item.research_question,
            'inclusion_criteria': item.inclusion_criteria or '',
            'exclusion_criteria': item.exclusion_criteria or '',
            'status': item.status,
        } for item in items]}), 200
    data = request.get_json(silent=True) or {}
    question = str(data.get('research_question', '')).strip()
    if not question:
        return jsonify({'error': 'Research question is required'}), 400
    review = SystematicReview(
        user_id=current_user.id,
        research_question=question,
        inclusion_criteria=str(data.get('inclusion_criteria', '')).strip(),
        exclusion_criteria=str(data.get('exclusion_criteria', '')).strip(),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'id': review.id, 'status': review.status}), 201

@systematic_bp.route('/reviews/<int:review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    review = review_for_user(review_id)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    data = request.get_json(silent=True) or {}
    if 'research_question' in data:
        review.research_question = str(data['research_question']).strip()
    if 'inclusion_criteria' in data:
        review.inclusion_criteria = str(data['inclusion_criteria']).strip()
    if 'exclusion_criteria' in data:
        review.exclusion_criteria = str(data['exclusion_criteria']).strip()
    if 'status' in data:
        status = str(data['status']).strip()
        current_index = STEPS.index(review.status) if review.status in STEPS else 0
        if status not in STEPS or STEPS.index(status) > current_index + 1:
            return jsonify({'error': 'Review must progress one step at a time'}), 400
        review.status = status
    db.session.commit()
    return jsonify({'status': review.status}), 200

@systematic_bp.route('/reviews/<int:review_id>/papers', methods=['GET', 'POST'])
@login_required
def papers(review_id):
    review = review_for_user(review_id)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    if request.method == 'GET':
        items = ReviewPaper.query.filter_by(review_id=review.id).order_by(ReviewPaper.created_at.asc()).all()
        return jsonify({'items': [{
            'id': item.id, 'title': item.title, 'authors': item.authors or '',
            'abstract': item.abstract or '', 'source': item.source or '', 'status': item.status,
        } for item in items]}), 200
    data = request.get_json(silent=True) or {}
    title = str(data.get('title', '')).strip()
    if not title:
        return jsonify({'error': 'Paper title is required'}), 400
    paper = ReviewPaper(review_id=review.id, title=title, authors=str(data.get('authors', '')).strip(),
                        abstract=str(data.get('abstract', '')).strip(), source=str(data.get('source', '')).strip())
    db.session.add(paper)
    db.session.commit()
    return jsonify({'id': paper.id}), 201

@systematic_bp.route('/reviews/<int:review_id>/papers/<int:paper_id>', methods=['PATCH'])
@login_required
def update_paper(review_id, paper_id):
    if not review_for_user(review_id):
        return jsonify({'error': 'Review not found'}), 404
    paper = ReviewPaper.query.filter_by(id=paper_id, review_id=review_id).first()
    if not paper:
        return jsonify({'error': 'Paper not found'}), 404
    status = str((request.get_json(silent=True) or {}).get('status', '')).strip().lower()
    if status not in {'pending', 'include', 'exclude', 'maybe'}:
        return jsonify({'error': 'Invalid screening decision'}), 400
    paper.status = status
    db.session.commit()
    return jsonify({'status': paper.status}), 200
