from groq import Groq
from flask import current_app

class GroqService:
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