from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app import db
from app.models import SearchHistory
from app.services.sources.arxiv_api import query_arxiv
from app.services.sources.pubmed_api import query_pubmed
from app.services.sources.crossref_api import query_crossref
from app.services.sources.core_api import query_core

papers_bp = Blueprint('papers', __name__)

SOURCE_QUERIES = {
    'arxiv': query_arxiv,
    'pubmed': query_pubmed,
    'crossref': query_crossref,
    'core': query_core,
}
SOURCE_LABELS = {
    'arxiv': 'arXiv',
    'pubmed': 'PubMed Central',
    'crossref': 'Crossref',
    'core': 'CORE',
}

def _year(value):
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None

def _matches_filters(paper, filters):
    year_filter = filters.get('date')
    paper_year = _year(paper.get('publication_date'))
    if year_filter and year_filter != 'any' and paper_year is not None:
        minimum = _year(year_filter)
        if minimum and paper_year < minimum:
            return False

    if filters.get('pdf_only') and not paper.get('pdf_url'):
        return False
    if filters.get('open_access') and not (paper.get('pdf_url') or paper.get('url')):
        return False

    searchable = ' '.join([
        str(paper.get('title', '')),
        str(paper.get('abstract', '')),
    ]).lower()
    study_types = filters.get('study_types', [])
    if study_types and not any(
        term.replace('-', ' ') in searchable for term in study_types
    ):
        return False
    return True

@papers_bp.route('/search', methods=['POST'])
@login_required
def search_papers():
    data = request.get_json(silent=True) or {}
    query = str(data.get('query', '')).strip()
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    if len(query) > 1000:
        return jsonify({'error': 'Search query is too long'}), 400

    selected_sources = [
        str(source).lower() for source in data.get('sources', SOURCE_QUERIES)
        if str(source).lower() in SOURCE_QUERIES
    ]
    if not selected_sources:
        return jsonify({'error': 'Select at least one source platform'}), 400

    filters = {
        'date': str(data.get('date', 'any')).lower(),
        'open_access': bool(data.get('open_access')),
        'pdf_only': bool(data.get('pdf_only')),
        'study_types': [str(item).lower() for item in data.get('study_types', [])],
    }
    all_results = []
    errors = []
    for source in selected_sources:
        try:
            results = SOURCE_QUERIES[source](query, 10)
            for paper in results:
                paper['source_key'] = source
                paper['source'] = paper.get('source') or SOURCE_LABELS[source]
                if _matches_filters(paper, filters):
                    all_results.append(paper)
        except Exception as error:
            errors.append(f'{SOURCE_LABELS[source]}: {error}')

    unique = {}
    for paper in all_results:
        key = (paper.get('doi') or paper.get('url') or paper.get('title', '')).lower()
        unique[key] = paper
    papers = list(unique.values())[:50]

    try:
        db.session.add(SearchHistory(
            user_id=current_user.id,
            query=query,
            research_mode='find_papers',
            selected_source=','.join(selected_sources),
            result_summary=f'{len(papers)} papers found',
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({
        'query': query,
        'papers': papers,
        'count': len(papers),
        'errors': errors,
    }), 200
