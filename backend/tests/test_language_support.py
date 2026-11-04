from app.routes.chat import get_system_prompt, rule_based_response
from app.services.ai_service import AIService


def test_hinglish_chat_prompt_requires_roman_script():
    prompt = get_system_prompt("hi-latn")

    assert "natural Hinglish" in prompt
    assert "Latin/Roman letters" in prompt
    assert "Never use Devanagari" in prompt


def test_hinglish_ai_instruction_is_used_by_shared_ai_service():
    instruction = AIService._get_language_instruction("hi-latn")

    assert "natural Hinglish" in instruction
    assert "Do not use Devanagari" in instruction


def test_hinglish_offline_chat_fallback_uses_roman_script():
    response = rule_based_response("fever", language="hi-latn")

    assert "Aapke 'fever' sawaal" in response
    assert not any("\u0900" <= character <= "\u097f" for character in response)
