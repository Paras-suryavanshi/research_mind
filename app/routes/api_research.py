from flask import Blueprint, request, jsonify, current_app
from uuid import uuid4
from datetime import datetime, timezone
from flask_login import login_required, current_user
from app.services.groq_service import GroqService
from app.services.research_selector import ResearchSelector
from app.services.pdf_processor import PDFProcessor
from app.models import SearchHistory, ChatHistory, ChatConversation, ChatMessage, Project
from app import db

research_bp = Blueprint('research', __name__)

@research_bp.route('/query', methods=['POST'])
@login_required
def execute_research_query():
    data = request.get_json(silent=True) or {}
    query = str(data.get('query', '')).strip()
    project_id = data.get('project_id')
    mode = str(data.get('mode', 'quick_qa')).strip() or 'quick_qa'
    response_length = str(data.get('response_length', 'medium')).strip().lower() or 'medium'
    if response_length not in {'low', 'medium', 'high'}:
        return jsonify({"error": "Invalid response length"}), 400
    
    if not query:
        return jsonify({"error": "Research query is required"}), 400
    if len(query) > 2000:
        return jsonify({"error": "Research query is too long"}), 400

    if GroqService.requires_safety_refusal(query):
        return jsonify({
            "data": GroqService.SAFE_REFUSAL,
            "papers": [],
            "source": "safety",
            "intent": "GENERAL_CHAT",
            "search_query": None,
        }), 200

    # Classify every input before any provider search is attempted.
    classification = GroqService.classify_research_input(query)
    if classification["error"]:
        return jsonify({"error": classification["error"]}), 500
    intent = classification["content"]["intent"]
    normalized_query = classification["content"]["search_query"]

    if intent == "UNCLASSIFIED":
        result = GroqService.generate_unclassified_response(query)
        if result["error"]:
            return jsonify({
                "data": "I couldn't determine exactly what you need. Could you clarify your request?",
                "papers": [],
                "source": "unclassified",
                "intent": intent,
                "search_query": None,
            }), 200
        return jsonify({
            "data": result["content"],
            "papers": [],
            "source": "unclassified",
            "intent": intent,
            "search_query": None,
        }), 200

    if intent == "GENERAL_CHAT":
        result = GroqService.generate_general_chat(query)
        if result["error"]:
            return jsonify({"error": result["error"]}), 500
        return jsonify({
            "data": result["content"],
            "papers": [],
            "source": "general_chat",
            "intent": intent,
            "search_query": None,
        }), 200

    search_query = normalized_query

    if project_id is not None:
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid project id"}), 400
        if not db.session.get(Project, project_id) or not Project.query.filter_by(
            id=project_id, user_id=current_user.id
        ).first():
            return jsonify({"error": "Project not found"}), 404

    # Step 1: Execute intelligent search across sources
    search_results = ResearchSelector.execute_search(search_query, max_results=5)
    source = search_results["source"]
    papers = search_results["papers"]
    
    # Step 2: Handle "No Results" cleanly as required
    if not papers:
        return jsonify({
            "data": "Sorry, we can't help with this topic as it is not available on any of the available research platforms.",
            "papers": [],
            "source": source,
            "intent": intent,
            "search_query": search_query,
        }), 200

    # Step 3: Format context for Groq
    context_str = ""
    for i, p in enumerate(papers):
        context_str += f"[{i+1}] Title: {p['title']}\nAuthors: {p['authors']}\nAbstract: {p['abstract']}\n\n"

    # Step 4: Construct System Prompt based on Mode
    length_guidance = {
        "low": "Keep the answer very short and concise: use minimal tokens, a brief summary, and only the most important findings and gap.",
        "medium": "Give a moderately detailed answer with enough explanation to make the reasoning clear, but remain focused and concise.",
        "high": "Give slightly more detail than Medium, while staying controlled and concise. Do not add filler, repetition, or unnecessarily long paper-by-paper descriptions."
    }[response_length]
    system_prompt = f"""You are an expert academic research assistant and evidence synthesizer.
Answer the user's research question by understanding and synthesizing the supplied papers.
Do not copy sentences, paste abstracts, or stitch together disconnected fragments. Write in your own words.
Reason like a researcher: establish what the question asks, connect converging and differing findings,
explain the evidence in a clear logical step-by-step flow, and distinguish evidence from interpretation.
Synthesize multiple papers around the question rather than describing Paper 1, Paper 2, and Paper 3 separately.
First check whether the papers directly match the requested topic. If they do not,
clearly say that the evidence is indirect instead of presenting unrelated papers as direct evidence.
When the user asks about a named paper, prioritize that paper's actual contribution.
{length_guidance}
Structure your response cleanly using markdown with the following sections:
### Research Summary
### Key Findings
### Important Evidence
### Research Gaps
Generate the summary, key points, findings, gaps, and other sections from the combined evidence in your own words.
Always cite supporting sources inline using the bracketed numbers provided [1], [2], etc.
Do not fabricate information or claim that a source says something not present in the context.
Use a Markdown table when presenting multiple papers, comparisons, risks, methods, or other
structured items with the same fields; otherwise use headings and concise paragraphs."""

    if mode == 'research_gaps':
        system_prompt = f"""You are an expert academic research assistant and evidence synthesizer.
Focus on identifying missing or underexplored areas by comparing and synthesizing the provided research.
Do not copy abstracts or list disconnected paper summaries. Explain the reasoning linking the evidence to each gap.
{length_guidance}
Structure your response with:
### Existing Research
### Important Findings
### Underexplored Areas
### Recommended Research Gaps
Use Markdown tables for structured comparisons or lists with consistent fields.
Use citations [1], [2], etc. and do not fabricate evidence."""

    if intent == "RESEARCH_QUESTION":
        user_request = f"""The user's original research question is:
{query}

The normalized literature search query is:
{search_query}"""
    else:
        user_request = f"""The user's research topic is:
{query}

The normalized literature search query is:
{search_query}"""

    prompt = f"""{user_request}

Research context:
{context_str}

Synthesize the evidence above into one coherent answer to the user's question.
Follow the selected response length exactly: {response_length}."""

    # Step 5: Generate analysis via automatically rotating API keys & fallback models
    result = GroqService.generate_research_content(
        prompt=prompt,
        system_prompt=system_prompt,
        response_length=response_length
    )

    if result["error"]:
        return jsonify({"error": result["error"]}), 500

    # Step 6: Save history to database safely
    try:
        history = SearchHistory(
            user_id=current_user.id,
            project_id=project_id,
            query=query,
            research_mode=mode,
            selected_source=source,
            result_summary=result["content"]
        )
        db.session.add(history)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to save research history")

    return jsonify({
        "data": result["content"],
        "papers": papers,
        "source": source,
        "intent": intent,
        "search_query": search_query,
    }), 200

@research_bp.route('/chat', methods=['POST'])
@login_required
def chat_with_paper():
    data = request.get_json(silent=True) or {}
    question = str(data.get('question', '')).strip()
    title = str(data.get('title', '')).strip()
    pdf_url = str(data.get('pdf_url', '')).strip()
    abstract = str(data.get('abstract', data.get('text', ''))).strip()
    raw_conversation_id = data.get('conversation_id')
    conversation_id = (
        str(raw_conversation_id).strip()
        if raw_conversation_id is not None
        else ''
    )
    if conversation_id.lower() in {'null', 'none', 'undefined'}:
        conversation_id = ''
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    if len(question) > 2000:
        return jsonify({"error": "Question is too long"}), 400
        
    conversation = None
    if conversation_id:
        conversation = ChatConversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first()
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
    else:
        conversation = ChatConversation(
            id=str(uuid4()), user_id=current_user.id,
            title=question[:255], pdf_url=pdf_url or None
        )
        db.session.add(conversation)
        db.session.flush()

    previous_messages = ChatMessage.query.filter_by(
        conversation_id=conversation.id
    ).order_by(ChatMessage.created_at.asc()).all()
    conversation_context = "\n".join(
        f"{message.role.title()}: {message.content}" for message in previous_messages[-10:]
    )
    context_text = abstract
    
    # Extract PDF text if URL is available
    if pdf_url and pdf_url.lower().startswith(('http://', 'https://')):
        extracted = PDFProcessor.extract_text_from_url(pdf_url)
        if extracted:
            context_text = extracted
            
    system_prompt = "You are a helpful research assistant. Answer the user's question based strictly on the provided paper text. Do not invent information."
    prompt = (
        f"Paper Title: {title or 'Unknown'}\n"
        f"Paper Content:\n{context_text or 'No paper text was provided.'}\n\n"
        f"Previous conversation:\n{conversation_context or 'None'}\n\n"
        f"User Question: {question}"
    )
    
    result = GroqService.generate_research_content(prompt=prompt, system_prompt=system_prompt)
    
    if result["error"]:
        return jsonify({"error": result["error"]}), 500

    try:
        conversation.updated_at = datetime.now(timezone.utc)
        db.session.add(ChatMessage(conversation_id=conversation.id, role='user', content=question))
        db.session.add(ChatMessage(conversation_id=conversation.id, role='assistant', content=result["content"]))
        db.session.add(ChatHistory(
            user_id=current_user.id,
            question=question,
            answer=result["content"],
            pdf_url=pdf_url or None,
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to save chat history")
        
    return jsonify({"data": result["content"], "conversation_id": conversation.id}), 200