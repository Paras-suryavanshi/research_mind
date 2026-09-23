import csv
import io

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

data_analysis_bp = Blueprint('data_analysis', __name__)

MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ROWS = 10000
MAX_COLUMNS = 100


@data_analysis_bp.route('/', methods=['POST'])
@login_required
def analyze_dataset():
    uploaded = request.files.get('file') or request.files.get('dataset')
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "A CSV or XLSX dataset is required"}), 400
    if request.content_length and request.content_length > MAX_FILE_BYTES:
        return jsonify({"error": "Dataset exceeds the 50MB limit"}), 413

    filename = uploaded.filename.rsplit('\\', 1)[-1].rsplit('/', 1)[-1]
    extension = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    if extension in ('xlsx', 'xls'):
        return jsonify({"error": "XLSX analysis requires the optional openpyxl dependency; CSV is supported"}), 415
    if extension != 'csv':
        return jsonify({"error": "Only CSV files are supported"}), 415

    raw = uploaded.stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        return jsonify({"error": "Dataset exceeds the 50MB limit"}), 413
    try:
        text = raw.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text))
        headers = next(reader, [])
        if not headers or len(headers) > MAX_COLUMNS:
            return jsonify({"error": "CSV must have a header row with at most 100 columns"}), 400
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                break
            rows.append(row[:MAX_COLUMNS])
    except (UnicodeDecodeError, csv.Error):
        return jsonify({"error": "CSV must be valid UTF-8"}), 400

    numeric_columns = []
    for index, header in enumerate(headers):
        values = []
        for row in rows:
            if index < len(row) and row[index].strip():
                try:
                    values.append(float(row[index]))
                except ValueError:
                    values = []
                    break
        if values:
            numeric_columns.append({
                "name": header,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": round(sum(values) / len(values), 6),
            })

    return jsonify({
        "filename": filename,
        "rows": len(rows),
        "columns": headers,
        "numeric_summary": numeric_columns,
        "prompt": str(request.form.get('prompt', '')).strip()[:2000],
        "message": "Basic CSV summary generated",
    }), 200
