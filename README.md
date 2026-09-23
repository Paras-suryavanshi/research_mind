# Research Mind

Research Mind is a Flask-based research workspace for finding academic papers, synthesizing evidence with Groq-powered language models, chatting with individual papers, managing research projects, and organizing review work.

The application combines provider-backed literature search with authenticated, database-backed research history, saved papers, documents, conversations, and systematic-review workflows.

## Features

- Authenticated user accounts with signup, login, logout, profile, and settings pages.
- Quick research question answering grounded in papers retrieved from research providers.
- Research-mode pages for:
  - Quick Q/A
  - Literature Review
  - Research Gaps
  - Systematic Review
- Intelligent source selection based on the research topic:
  - PubMed for medical and biomedical topics
  - arXiv for physics, mathematics, computer science, and AI topics
  - Crossref for broad scholarly metadata searches
  - CORE for broad open-access repository searches, with Crossref fallback
- Find Papers search with source, publication-date, access, PDF, and study-type filters.
- Paper result actions including:
  - Chat with Paper
  - Add to Library
  - View PDF when a PDF URL is available
- Paper chat with extracted PDF context, persistent conversations, and follow-up questions.
- Markdown response rendering, including headings, lists, tables, emphasis, code, and formatted research sections.
- Research response-length controls for concise, balanced, or more detailed answers.
- Search history and reopenable chat history.
- User library for saved papers and uploaded documents.
- Project creation and project-scoped research data.
- AI Writer tools and saved documents.
- Systematic Review workflow:
  - Setup
  - Screening
  - Extraction
  - Analysis
  - Report
- Include, Exclude, and Maybe screening decisions for review papers.
- Data-analysis endpoint and presentation/paraphrasing tool pages.

## Technology Stack

### Backend

- Python
- Flask 3.0.3
- Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Flask-Bcrypt 1.0.1
- SQLite by default
- Requests for external provider requests
- PyPDF2 for PDF text extraction
- Beautiful Soup 4 for HTML/XML parsing
- python-dotenv for environment configuration
- Groq Python client for LLM generation

### Frontend

- Jinja2-rendered HTML templates
- Vanilla JavaScript
- CSS stylesheets
- SVG logo and interface assets
- Markdown-style response renderers implemented in the templates

## Project Structure

```text
research_mind/
├── app/
│   ├── __init__.py              # Flask application factory and extensions
│   ├── config.py                # Environment-backed application configuration
│   ├── models.py                # SQLAlchemy models
│   ├── routes/                  # Page and API blueprints
│   ├── services/
│   │   ├── groq_service.py      # Groq model/key rotation and generation
│   │   ├── pdf_processor.py     # PDF text extraction
│   │   ├── research_selector.py # Provider selection and result ranking
│   │   └── sources/              # PubMed, arXiv, Crossref, and CORE adapters
│   ├── static/
│   │   ├── css/
│   │   ├── img/
│   │   └── js/
│   └── templates/                # Auth, dashboard, feature, and tool pages
├── instance/
│   └── research_mind.db          # Local SQLite database created at runtime
├── requirements.txt
├── run.py                        # Development entry point
└── .env                          # Local environment variables; do not commit
```

## Architecture

The application uses a Flask application factory in `app/__init__.py`. The factory initializes:

- SQLAlchemy for persistence
- Flask-Login for session authentication
- Flask-Bcrypt for password hashing
- Page and API blueprints

Research requests follow this general flow:

1. An authenticated user submits a research query.
2. `ResearchSelector` chooses a provider using topic heuristics.
3. The selected provider adapter retrieves normalized paper records.
4. Results are ranked for topic and title relevance.
5. The paper metadata is placed into an evidence context.
6. `GroqService` sends the context and research prompt to Groq.
7. The result and search metadata are persisted in the user’s history.
8. The frontend renders the response and source citations.

The default database is SQLite at `instance/research_mind.db`. The application creates the SQLite parent directory when needed, and `run.py` calls `db.create_all()` before starting the development server.

## Requirements

- Python 3.10 or newer is recommended.
- Internet access is required for external research-provider and Groq requests.
- A Groq API key is required for AI-generated answers, paper chat, and other Groq-backed tools.
- A CORE API key is optional. CORE searches require it; the research selector falls back to Crossref when CORE is unavailable.

## Installation

From the project root:

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root. The file is intentionally ignored by Git.

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
APP_ENV=development

GROQ_API_KEY_1=your-groq-api-key
# Optional additional keys used by the Groq key rotation pool:
GROQ_API_KEY_2=
GROQ_API_KEY_3=
GROQ_API_KEY_4=
GROQ_API_KEY_5=

# Optional; required for CORE provider searches:
CORE_API_KEY=your-core-api-key
```

### Configuration notes

- `SECRET_KEY` signs Flask sessions. Use a strong value outside local development.
- Local development always defaults to SQLite at `instance/research_mind.db`.
- Production requires `APP_ENV=production` and a `DATABASE_URL` value. On Render, set `DATABASE_URL` to the Render PostgreSQL Internal Database URL. The application also uses a provided `DATABASE_URL` automatically if `APP_ENV` was not set by the deployment environment.
- The configuration also accepts the legacy `postgres://` PostgreSQL scheme and normalizes it for SQLAlchemy.
- At least one `GROQ_API_KEY_*` value should be configured for AI functionality.
- Multiple Groq keys can be supplied; the service rotates through configured keys and model fallbacks when requests fail.
- `CORE_API_KEY` is optional because CORE requests are skipped without a key and the selector can fall back to Crossref.

## Running the Application

With the virtual environment activated and `.env` configured:

```powershell
python run.py
```

Or on macOS/Linux:

```bash
python run.py
```

The development server listens on:

```text
http://127.0.0.1:5000
```

`run.py` starts Flask in debug mode, binds to `0.0.0.0`, initializes missing database tables, and serves the application on port `5000`.

## Basic Usage

1. Open the application in a browser.
2. Create an account or sign in.
3. Use **Quick Q/A** to ask a research question.
4. Choose a response-length setting in the input Settings control when needed.
5. Review the generated synthesis and cited papers.
6. Use **Find Papers** to search across supported sources and apply filters.
7. Save relevant papers to **Library** or open **Chat with Paper** for paper-specific questions and follow-ups.
8. Use **Literature Review** or **Research Gaps** for focused evidence synthesis.
9. Create a **Systematic Review** and progress through setup, screening, extraction, analysis, and report stages.
10. Reopen prior queries and conversations from **History**.

## Pages

The main page routes include:

| Route | Purpose |
|---|---|
| `/` | Public landing page |
| `/login` | Login page |
| `/signup` | Account creation page |
| `/dashboard` | Quick Q/A research workspace |
| `/literature-review` | Literature Review workspace |
| `/research-gaps` | Research Gaps workspace |
| `/systematic-review` | Systematic Review workspace |
| `/find-papers` | Provider-backed paper search |
| `/paper-chat` | Chat with a selected paper |
| `/library` | Saved papers and documents |
| `/history` | Search and chat history |
| `/projects` | Research project management |
| `/ai-writer` | AI writing workspace |
| `/data-analysis` | Data-analysis workspace |
| `/presentation` | Academic presentation workspace |
| `/paraphraser` | Academic paraphrasing tool |

## API Overview

All API routes requiring a user session use the authenticated account to scope stored data.

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/signup` | Create an account |
| `POST /api/auth/login` | Authenticate a user |
| `POST /api/auth/logout` | End the current session |
| `POST /api/research/query` | Search literature and generate a research answer |
| `POST /api/research/chat` | Ask questions about a paper and continue a conversation |
| `POST /api/papers/search` | Search and filter papers |
| `GET /api/history/searches` | Load saved search history |
| `GET /api/history/chats` | List saved conversations |
| `GET /api/history/chats/<conversation_id>` | Load a saved conversation |
| `GET/POST /api/library/` | List or save library items |
| `DELETE /api/library/<item_id>` | Remove a library item |
| `POST /api/library/documents` | Upload a library document |
| `GET/POST /api/projects/` | List or create projects |
| `PUT/DELETE /api/projects/<project_id>` | Update or delete a project |
| `GET/POST /api/systematic/reviews` | List or create systematic reviews |
| `PUT /api/systematic/reviews/<review_id>` | Update review setup or workflow state |
| `GET/POST /api/systematic/reviews/<review_id>/papers` | List or add review papers |
| `PATCH /api/systematic/reviews/<review_id>/papers/<paper_id>` | Update a screening decision |
| `POST /api/ai_writer/tools` | Run an AI Writer tool |
| `GET/POST /api/ai_writer/documents` | Load or save AI Writer documents |
| `POST /api/data-analysis/` | Submit a data-analysis request |

## Data and Privacy

The local SQLite database contains user accounts, password hashes, project data, search history, chat conversations, library records, documents, and systematic-review data. Keep the database and `.env` file private.

The project’s `.gitignore` excludes local secrets, the SQLite database, Python caches, virtual environments, logs, IDE files, and other generated artifacts. Do not commit API keys or real user data.

## Development Checks

Compile the Python application to catch syntax errors:

```powershell
python -m compileall -q app run.py
```

When changing inline frontend JavaScript, extract the relevant script and validate it with Node.js:

```powershell
node --check path\to\script.js
```

The repository does not currently define a dedicated test runner configuration. For functional changes, use the Flask test client or manually verify the affected authenticated page and API flow.

## External Research Sources

Research provider adapters are located in `app/services/sources/`:

- `pubmed_api.py`
- `arxiv_api.py`
- `crossref_api.py`
- `core_api.py`

Provider responses are normalized into paper records containing fields such as title, authors, abstract, publication date, source, DOI, URL, and PDF URL where available.

## License

No license file is currently included in the project. Add a license before distributing the application or accepting external contributions.
