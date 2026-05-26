"""Gemini client — never exposes raw RAG chunks to the user."""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "counselling_system.txt"


def resolve_api_key(explicit: str | None = None) -> str:
    """Get API key, preferring key rotation manager for auto load-balancing."""
    if explicit:
        return explicit.strip()
    
    try:
        from ai_engine.gemini.key_manager import get_api_key
        key = get_api_key()
        if key:
            return key
    except Exception:
        pass
    
    # Fallback to single key from settings/env
    try:
        from django.conf import settings
        key = getattr(settings, "GEMINI_API_KEY", "") or ""
        if key:
            return key.strip()
    except Exception:
        pass
    
    import os
    return (os.getenv("GEMINI_API_KEY") or "").strip()


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = resolve_api_key(api_key)
        self.model = model or self._default_model()
        self._configured = False
        self.last_error: str | None = None

    def _default_model(self) -> str:
        try:
            from django.conf import settings

            return getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
        except Exception:
            return "gemini-2.0-flash"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _configure(self) -> None:
        if self._configured or not self.api_key:
            return
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        self._configured = True

    def load_system_prompt(self) -> str:
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        return "You are an expert JoSAA counselling assistant."

    def generate(
        self,
        user_message: str,
        structured_data: str = "",
        rag_context: str = "",
        history: list[dict] | None = None,
        fallback_text: str = "",
    ) -> str:
        """Generate reply. On failure, return fallback_text (never raw RAG)."""
        if not self.available:
            self.last_error = "GEMINI_API_KEY not set"
            return fallback_text or (
                "AI is not configured. Add `GEMINI_API_KEY` to a `.env` file at the project root "
                "and restart the Django server."
            )

        try:
            self._configure()
            import google.generativeai as genai

            model = genai.GenerativeModel(
                self.model,
                system_instruction=self.load_system_prompt(),
            )

            # RAG is internal context only — instruct model not to quote filenames
            internal = []
            if structured_data:
                internal.append(
                    "INTERNAL_DATA (use college names/ranks only):" + structured_data
                )
            if rag_context:
                internal.append(
                    "INTERNAL_NOTES (summarize, never quote filenames):" + rag_context
                )

            prompt_parts = internal + [f"Q:{user_message}"]

            chat = model.start_chat(
                history=[
                    {"role": m["role"], "parts": [m["content"]]}
                    for m in (history or [])
                    if m.get("role") in ("user", "model")
                ]
            )
            response = chat.send_message("\n".join(prompt_parts))
            text = (response.text or "").strip()
            if text:
                # Mark key as successful
                try:
                    from ai_engine.gemini.key_manager import mark_key_success
                    mark_key_success(self.api_key)
                except Exception:
                    pass
                return text
            self.last_error = "Empty response from Gemini"
        except Exception as exc:
            logger.exception("Gemini API error")
            self.last_error = str(exc)
            
            # Mark key as errored for rotation
            try:
                from ai_engine.gemini.key_manager import mark_key_error
                error_type = "rate_limit" if "429" in str(exc) else "network"
                mark_key_error(self.api_key, error_type)
            except Exception:
                pass

        return fallback_text or (
            f"I could not reach the AI service ({self.last_error}). "
            "Below is guidance from our cutoff database instead."
        )
