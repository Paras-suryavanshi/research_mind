from pathlib import Path

# Existing project folder
ROOT = Path("research_mind")

# Exact folder structure
directories = [
    "app",
    "app/routes",
    "app/services",
    "app/services/sources",
    "app/static",
    "app/static/css",
    "app/static/js",
    "app/static/img",
    "app/static/img/icons",
    "app/templates",
    "app/templates/auth",
    "app/templates/dashboard",
    "app/templates/tools",
    "app/templates/features",
    "app/templates/user",
    "instance",
]

# Exact files
files = [
    ".env",
    "requirements.txt",
    "run.py",

    "app/__init__.py",
    "app/config.py",
    "app/models.py",

    "app/routes/__init__.py",
    "app/routes/auth_routes.py",
    "app/routes/page_routes.py",
    "app/routes/api_research.py",
    "app/routes/api_projects.py",
    "app/routes/api_library.py",
    "app/routes/api_ai_writer.py",
    "app/routes/api_user.py",

    "app/services/__init__.py",
    "app/services/groq_service.py",
    "app/services/research_selector.py",
    "app/services/pdf_processor.py",

    "app/services/sources/__init__.py",
    "app/services/sources/arxiv_api.py",
    "app/services/sources/crossref_api.py",
    "app/services/sources/core_api.py",
    "app/services/sources/pubmed_api.py",

    "app/static/css/style.css",
    "app/static/css/layout.css",
    "app/static/css/components.css",

    "app/static/js/main.js",
    "app/static/js/auth.js",
    "app/static/js/research.js",
    "app/static/js/ai_writer.js",
    "app/static/js/paper_chat.js",
    "app/static/js/library.js",

    "app/static/img/logo.svg",

    "app/templates/base.html",
    "app/templates/index.html",

    "app/templates/auth/login.html",
    "app/templates/auth/signup.html",

    "app/templates/dashboard/main.html",
    "app/templates/dashboard/literature_review.html",
    "app/templates/dashboard/systematic_review.html",
    "app/templates/dashboard/research_gaps.html",
    "app/templates/dashboard/presentation.html",
    "app/templates/dashboard/data_analysis.html",

    "app/templates/tools/find_papers.html",
    "app/templates/tools/paper_chat.html",
    "app/templates/tools/paraphraser.html",
    "app/templates/tools/trial_landscape.html",

    "app/templates/features/ai_writer.html",
    "app/templates/features/library.html",
    "app/templates/features/projects.html",
    "app/templates/features/history.html",

    "app/templates/user/settings.html",
    "app/templates/user/profile.html",
    "app/templates/user/upgrade.html",

    "instance/research_mind.db",
]


def create_structure():
    if not ROOT.exists():
        print(f"ERROR: '{ROOT}' folder does not exist.")
        print("Please create the research_mind folder first.")
        return

    # Create directories
    for directory in directories:
        path = ROOT / directory
        path.mkdir(parents=True, exist_ok=True)

    # Create files without overwriting existing files
    for file in files:
        path = ROOT / file
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            path.touch()

    print("\nResearch Mind structure created successfully.")
    print(f"Location: {ROOT.resolve()}")


if __name__ == "__main__":
    create_structure()