from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

page_bp = Blueprint('pages', __name__)

@page_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
    return render_template('index.html')

@page_bp.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
    return render_template('auth/login.html')

@page_bp.route('/forgot-password')
def forgot_password():
    return render_template('auth/forgot_password.html')

@page_bp.route('/signup')
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
    return render_template('auth/signup.html')

@page_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/main.html')

@page_bp.route('/library')
@login_required
def library():
    return render_template('features/library.html')

@page_bp.route('/ai-writer')
@login_required
def ai_writer():
    return render_template('features/ai_writer.html')

@page_bp.route('/systematic-review')
@login_required
def systematic_review():
    return render_template('dashboard/systematic_review.html')

@page_bp.route('/find-papers')
@login_required
def find_papers():
    return render_template('tools/find_papers.html')

@page_bp.route('/paper-chat')
@login_required
def paper_chat():
    return render_template('tools/paper_chat.html')

@page_bp.route('/paraphraser')
@login_required
def paraphraser():
    return render_template('tools/paraphraser.html')

@page_bp.route('/trial-landscape')
@login_required
def trial_landscape():
    return render_template('tools/trial_landscape.html')

@page_bp.route('/literature-review')
@login_required
def literature_review():
    return render_template('dashboard/literature_review.html')

@page_bp.route('/research-gaps')
@login_required
def research_gaps():
    return render_template('dashboard/research_gaps.html')

@page_bp.route('/presentation')
@login_required
def presentation():
    return render_template('dashboard/presentation.html')

@page_bp.route('/data-analysis')
@login_required
def data_analysis():
    return render_template('dashboard/data_analysis.html')

@page_bp.route('/projects')
@login_required
def projects():
    return render_template('features/projects.html')

@page_bp.route('/history')
@login_required
def history():
    return render_template('features/history.html')

@page_bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html')

@page_bp.route('/settings')
@login_required
def settings():
    return render_template('user/settings.html')

@page_bp.route('/upgrade')
@login_required
def upgrade():
    return render_template('user/upgrade.html')