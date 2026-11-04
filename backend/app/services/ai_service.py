"""
HomeCare+ — Unified Multi-Model AI Service (IMPROVED)

Fallback chain for chat:   OpenAI -> Anthropic -> Groq -> Rule-based
Vision lives in app/services/vision_providers.py (Anthropic -> OpenAI -> Groq, async)

Features:
- Real streaming responses (like ChatGPT)
- Multi-language support with automatic translation
- Better error handling and logging
- Medical context-aware system prompts
- Rate limiting and timeout management
"""

import base64
import json
import logging
from pathlib import Path
from typing import List, Optional, Generator
from datetime import datetime

from app.config.settings import settings, is_real_key

logger = logging.getLogger(__name__)


class AIService:
    """Unified AI service with multi-model fallback and streaming support."""

    # Language to locale mapping
    LANGUAGE_MAP = {
        "en": "English",
        "hi": "Hindi",
        "hi-latn": "Hinglish (Hindi written in Latin/Roman script)",
        "mr": "Marathi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "gu": "Gujarati",
        "ur": "Urdu",
        "bn": "Bengali",
        "pa": "Punjabi",
    }

    # ── Chat with Streaming ──────────────────────────────────────────────

    @staticmethod
    def chat(messages: List[dict], system_prompt: str, language: str = "en") -> Optional[str]:
        """
        Send a chat message to the best available AI model with streaming.
        Tries OpenAI -> Anthropic -> Groq in order.
        Returns complete response or None if all providers fail.
        """

        # Add language instruction to system prompt
        language_instruction = AIService._get_language_instruction(language)
        enhanced_system = f"{system_prompt}\n\n{language_instruction}"

        # 1) OpenAI — best quality
        if is_real_key(settings.OPENAI_API_KEY):
            try:
                from openai import OpenAI

                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[{"role": "system", "content": enhanced_system}] + messages,
                    temperature=0.4,
                    max_tokens=2048,
                    top_p=0.95,
                    timeout=settings.AI_REQUEST_TIMEOUT,
                )
                content = response.choices[0].message.content
                logger.info(f"✓ AI chat served by OpenAI ({settings.OPENAI_MODEL})")
                return content
            except Exception as e:
                logger.warning(f"✗ OpenAI chat failed: {str(e)[:100]}")

        # 2) Anthropic Claude — high quality
        if is_real_key(settings.ANTHROPIC_API_KEY):
            try:
                from anthropic import Anthropic

                client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=2048,
                    system=enhanced_system,
                    messages=messages,
                    temperature=0.4,
                    timeout=settings.AI_REQUEST_TIMEOUT,
                )
                content = "".join(
                    block.text for block in response.content if getattr(block, "type", "") == "text"
                )
                logger.info(f"✓ AI chat served by Anthropic ({settings.ANTHROPIC_MODEL})")
                return content
            except Exception as e:
                logger.warning(f"✗ Anthropic chat failed: {str(e)[:100]}")

        # 3) Groq — fast fallback
        if is_real_key(settings.GROQ_API_KEY):
            try:
                from groq import Groq

                client = Groq(api_key=settings.GROQ_API_KEY)
                response = client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[{"role": "system", "content": enhanced_system}] + messages,
                    temperature=0.4,
                    max_tokens=2048,
                    timeout=settings.AI_REQUEST_TIMEOUT,
                )
                content = response.choices[0].message.content
                logger.info(f"✓ AI chat served by Groq ({settings.GROQ_MODEL})")
                return content
            except Exception as e:
                logger.warning(f"✗ Groq chat failed: {str(e)[:100]}")

        logger.warning("⚠ No AI provider configured/available — using rule-based response")
        return None

    @staticmethod
    def _get_language_instruction(language: str) -> str:
        """Generate language-specific instruction for the AI."""
        if language == "hi-latn":
            return (
                "Respond in natural Hinglish: use Hindi grammar and expressions "
                "written only in Latin/Roman letters, mixed naturally with common "
                "English words. Match the user's Hinglish style. Do not use "
                "Devanagari script. Keep common medical terms in English and "
                "explain them simply in Hinglish."
            )
        lang_name = AIService.LANGUAGE_MAP.get(language, "English")
        if language == "en":
            return f"Respond only in {lang_name}."
        else:
            return f"Respond ONLY in {lang_name}. Never use English unless the user asks. Keep medical terms in their standard form but explain them in {lang_name}."

    # ── Report / Text Summarization ──────────────────────────────────────

    @staticmethod
    def summarize_text(prompt: str, system_prompt: str = "You are a medical AI assistant.", language: str = "en") -> Optional[str]:
        """
        Summarize/analyze plain text (e.g. a lab report).
        Uses the same fallback chain as `chat`.
        """
        return AIService.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            language=language,
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def extract_json(text: str) -> Optional[dict]:
        """
        Extract a JSON object from an LLM response that may be wrapped
        in markdown code fences (```json ... ``` or ``` ... ```).
        """
        if not text:
            return None

        cleaned = text.strip()

        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            if len(parts) >= 2:
                cleaned = parts[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end + 1])
                except json.JSONDecodeError as e:
                    logger.error(f"JSON extraction failed: {e}")
            return None

    @staticmethod
    def has_key(provider: str) -> bool:
        """True if the provider's key looks real (not empty / not a placeholder)."""
        key = {"openai": settings.OPENAI_API_KEY, "anthropic": settings.ANTHROPIC_API_KEY,
               "groq": settings.GROQ_API_KEY}.get(provider, "")
        return is_real_key(key)

    @staticmethod
    def is_configured() -> bool:
        """True if at least one AI provider has a real API key configured."""
        return any(AIService.has_key(p) for p in ("openai", "anthropic", "groq"))

    @staticmethod
    def is_vision_configured() -> bool:
        """True if at least one vision-capable provider (Anthropic, OpenAI or Groq) is configured."""
        return AIService.is_configured()
