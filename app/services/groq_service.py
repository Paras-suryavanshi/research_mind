import json
import re
from groq import Groq
from flask import current_app

class GroqService:
    SAFE_REFUSAL = "I’m sorry, but I can’t assist with that request. I can help with a safe and appropriate alternative if you’d like."
    _current_key_index = 0
    _models = [
        "openai/gpt-oss-120b", 
        "openai/gpt-oss-20b"
    ]

    @classmethod
    def _get_next_key(cls, keys):
        if not keys:
            raise ValueError("No Groq API keys configured in the environment.")
        
        key = keys[cls._current_key_index]
        cls._current_key_index = (cls._current_key_index + 1) % len(keys)
        return key

    @classmethod
    def generate_research_content(
        cls,
        prompt,
        system_prompt="You are an expert academic research assistant. Provide structured, accurate, and objective information.",
        response_length="medium"
    ):
        keys = current_app.config.get('GROQ_API_KEYS', [])
        if not keys:
            return {"error": "Internal Backend Error: API keys missing from configuration.", "content": None}
        
        max_tokens_by_length = {"low": 700, "medium": 1400, "high": 2200}
        max_tokens = max_tokens_by_length.get(response_length, max_tokens_by_length["medium"])
        attempts = len(keys)
        last_error = None

        for _ in range(attempts):
            current_key = cls._get_next_key(keys)
            try:
                client = Groq(api_key=current_key)
            except Exception as e:
                last_error = str(e)
                current_app.logger.warning(
                    "Unable to initialize Groq client for key slot %s: %s",
                    cls._current_key_index,
                    e,
                )
                continue
            
            for model in cls._models:
                current_app.logger.info("Calling Groq model: %s", model)
                try:
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        model=model,
                        temperature=0.2,
                        max_tokens=max_tokens
                    )
                    current_app.logger.info("Groq model completed successfully: %s", model)
                    return {"content": response.choices[0].message.content, "error": None}
                
                except Exception as e:
                    error_msg = str(e).lower()
                    last_error = str(e)
                    current_app.logger.warning("Groq model failed: %s (%s)", model, e)
                    
                    if any(err in error_msg for err in ["rate limit", "too many requests", "quota", "unauthorized", "invalid api key"]):
                        # The key itself is restricted. Break the model loop and rotate to the next key.
                        break
                    else:
                        # It might be a model-specific failure (e.g. 120b overloaded). Continue to the 20b fallback.
                        continue
            
            # If we reach here without returning, either both models failed, or the key was rate limited.
            # The outer loop will automatically rotate to the next key and start over.
            
        return {
            "error": "All available AI processing keys and models failed. Please try again in a few moments.", 
            "content": None,
            "debug_error": last_error
        }

    @classmethod
    def classify_research_input(cls, user_input):
        system_prompt = """You classify a user's message for a research assistant.
Return JSON only, with exactly these keys:
{"intent":"RESEARCH_TOPIC|RESEARCH_QUESTION|GENERAL_CHAT","search_query":"normalized query or null"}

RESEARCH_TOPIC is a subject or area the user wants to research.
RESEARCH_QUESTION requires research papers or literature to answer.
GENERAL_CHAT is ordinary conversation that does not need research papers.
Requests for explicit sexual instructions must not be treated as research requests.
If a poorly phrased or ambiguous message appears research-related, prefer a research intent.
For research intents, normalize the message into one concise academic search query.
Preserve the user's actual intent and never invent a different topic.
For GENERAL_CHAT, search_query must be null."""
        prompt = f"Classify this user input:\n{user_input}"
        result = cls._generate(prompt, system_prompt, max_tokens=180)
        parsed = cls._parse_classification(result.get("content"))
        if parsed is not None:
            return {"content": parsed, "error": None}

        current_app.logger.warning(
            "Initial research intent classification failed; retrying with strict JSON prompt."
        )
        retry_prompt = f"""Return only one valid JSON object and no other text.
Do not use Markdown fences, explanations, or commentary.
Allowed intents are exactly RESEARCH_TOPIC, RESEARCH_QUESTION, GENERAL_CHAT.
Use a concise academic search_query for the first two intents and null for GENERAL_CHAT.

User input:
{user_input}"""
        retry_system_prompt = (
            "You are a strict JSON classifier. Output one syntactically valid JSON object only."
        )
        retry_result = cls._generate(retry_prompt, retry_system_prompt, max_tokens=120)
        parsed = cls._parse_classification(retry_result.get("content"))
        if parsed is not None:
            return {"content": parsed, "error": None}

        current_app.logger.warning(
            "Research intent classification failed after retry; using UNCLASSIFIED fallback."
        )
        return {
            "content": {"intent": "UNCLASSIFIED", "search_query": None},
            "error": None,
        }

    @classmethod
    def _parse_classification(cls, content):
        try:
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty classifier response")
            content = content.strip()
            if "{" in content and "}" in content:
                content = content[content.find("{"):content.rfind("}") + 1]
            parsed = json.loads(content)
            intent = parsed.get("intent")
            query = parsed.get("search_query")
            if intent not in {"RESEARCH_TOPIC", "RESEARCH_QUESTION", "GENERAL_CHAT"}:
                raise ValueError("Invalid classifier intent")
            if intent == "GENERAL_CHAT":
                query = None
            elif not isinstance(query, str) or not query.strip():
                raise ValueError("Research intent has no normalized query")
            else:
                query = query.strip()[:2000]
            return {"intent": intent, "search_query": query}
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            current_app.logger.warning("Invalid research intent response: %s", error)
            return None

    @classmethod
    def generate_general_chat(cls, user_input):
        return cls._generate(
            prompt=user_input,
            system_prompt="""You are a concise, friendly general assistant.
Answer ordinary conversation naturally in a few sentences. Do not discuss research papers unless asked.
Do not provide explicit sexual instructions or other harmful/inappropriate content.
For an explicit sexual-instruction request, reply exactly:
I’m sorry, but I can’t assist with that request. I can help with a safe and appropriate alternative if you’d like.""",
            max_tokens=250,
        )

    @classmethod
    def generate_unclassified_response(cls, user_input):
        return cls._generate(
            prompt=user_input,
            system_prompt="""You are a concise, safe, and helpful assistant.
The user's message could not be confidently classified. Respond based only on the input itself.
If it appears research-related, briefly explain or clarify what the user may be asking without searching papers.
If it is ordinary conversation, respond naturally.
Ask one short clarifying question when the intent is unclear.
Keep the response concise. Do not invent facts, provide harmful instructions, or discuss unrelated topics.""",
            max_tokens=250,
        )

    @classmethod
    def requires_safety_refusal(cls, user_input):
        normalized = re.sub(r"\s+", " ", user_input.lower()).strip()
        explicit_markers = (
            "explicit sexual instruction",
            "explicit sexual instructions",
            "sexual act",
            "sex act",
            "sexual activity",
        )
        instruction_markers = (
            "how do i",
            "how to",
            "instructions",
            "steps",
            "tell me how",
            "guide me",
        )
        sexual_instruction = any(marker in normalized for marker in explicit_markers) and any(
            marker in normalized for marker in instruction_markers
        )
        harmful_instruction = any(marker in normalized for marker in (
            "seriously hurt someone",
            "seriously harm someone",
            "injure someone",
            "kill someone",
            "murder someone",
            "attack someone",
        )) and any(marker in normalized for marker in instruction_markers)
        return sexual_instruction or harmful_instruction

    @classmethod
    def _generate(cls, prompt, system_prompt, max_tokens):
        keys = current_app.config.get('GROQ_API_KEYS', [])
        if not keys:
            return {"error": "Internal Backend Error: API keys missing from configuration.", "content": None}
        last_error = None
        for _ in range(len(keys)):
            current_key = cls._get_next_key(keys)
            try:
                client = Groq(api_key=current_key)
            except Exception as error:
                last_error = str(error)
                current_app.logger.warning("Unable to initialize Groq client: %s", error)
                continue
            for model in cls._models:
                current_app.logger.info("Calling Groq model: %s", model)
                try:
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        model=model,
                        temperature=0.1,
                        max_tokens=max_tokens,
                    )
                    return {"content": response.choices[0].message.content, "error": None}
                except Exception as error:
                    last_error = str(error)
                    current_app.logger.warning("Groq model failed: %s (%s)", model, error)
        return {"error": "All available AI processing keys and models failed. Please try again in a few moments.", "content": None, "debug_error": last_error}