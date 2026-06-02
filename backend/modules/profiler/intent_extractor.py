import google.generativeai as genai
import json
import asyncio
import re
from typing import Optional

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

INTENT_SYSTEM_PROMPT = """You are a cybersecurity threat analyst. Analyze the following attack conversation
and extract the attacker's profile. Return ONLY valid JSON with this exact structure:
{
  "primary_intent": "brief description of what attacker wanted",
  "target_assets": ["asset1", "asset2"],
  "sophistication_level": "SCRIPT_KIDDIE|INTERMEDIATE|ADVANCED|NATION_STATE",
  "motive": "data_theft|espionage|sabotage|financial|reconnaissance|other",
  "confidence": 0.85
}"""

INTENT_KEYWORDS = {
    "data_theft": ["user", "customer", "personal", "export", "dump", "extract", "steal"],
    "espionage": ["intel", "information", "secrets", "proprietary", "internal", "confidential"],
    "sabotage": ["delete", "destroy", "crash", "break", "disable", "shutdown"],
    "financial": ["payment", "financial", "credit card", "bank", "transaction", "money"],
    "reconnaissance": ["access", "capability", "what can", "how does", "permissions", "system"],
}

ASSET_KEYWORDS = {
    "Customer PII": ["user", "customer", "personal", "email", "phone", "address"],
    "Credentials": ["password", "credential", "key", "token", "secret", "auth"],
    "Financial Records": ["financial", "payment", "transaction", "billing", "invoice"],
    "System Access": ["admin", "root", "system", "access", "permission", "privilege"],
    "Internal Communications": ["email", "message", "slack", "internal", "communication"],
    "Source Code": ["code", "repository", "github", "source", "codebase"],
    "API Keys": ["api key", "api_key", "token", "secret key", "access key"],
}

SOPHISTICATION_INDICATORS = {
    "NATION_STATE": ["supply chain", "zero-day", "apt", "persistent", "living off the land", "lateral movement"],
    "ADVANCED": ["multi-step", "staged", "obfuscated", "evasion", "privilege escalation", "persistence"],
    "INTERMEDIATE": ["injection", "bypass", "manipulation", "exploit", "vulnerability"],
    "SCRIPT_KIDDIE": ["ignore previous", "dan mode", "jailbreak", "developer mode", "sudo"],
}


class IntentExtractor:
    def __init__(self):
        self._model = None
        self._configured = False
        if settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self._model = genai.GenerativeModel(settings.gemini_model)
                self._configured = True
            except Exception as e:
                logger.warning(f"Intent extractor Gemini config failed: {e}")

    async def extract(self, conversation: str, attack_type: str) -> dict:
        if self._configured and self._model:
            try:
                return await self._gemini_extract(conversation, attack_type)
            except Exception as e:
                logger.warning(f"Gemini intent extraction failed, using heuristic: {e}")
        return self._heuristic_extract(conversation, attack_type)

    async def _gemini_extract(self, conversation: str, attack_type: str) -> dict:
        prompt = f"""Attack type: {attack_type}
Conversation:
{conversation[:2000]}

Analyze and return the JSON profile."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                [INTENT_SYSTEM_PROMPT, prompt],
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=300,
                ),
            ),
        )

        text = response.text.strip()
        json_match = re.search(r"\{.*?\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return self._heuristic_extract(conversation, attack_type)

    def _heuristic_extract(self, conversation: str, attack_type: str) -> dict:
        lower = conversation.lower()

        motive = "reconnaissance"
        for m, keywords in INTENT_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                motive = m
                break

        target_assets = []
        for asset, keywords in ASSET_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                target_assets.append(asset)

        sophistication = "SCRIPT_KIDDIE"
        for level in ["NATION_STATE", "ADVANCED", "INTERMEDIATE"]:
            if any(ind in lower for ind in SOPHISTICATION_INDICATORS[level]):
                sophistication = level
                break

        intent_map = {
            "PROMPT_INJECTION": "Override AI agent safety controls",
            "JAILBREAK": "Remove ethical constraints from AI system",
            "IDENTITY_SPOOFING": "Gain unauthorized administrative access",
            "DATA_EXFILTRATION": "Extract sensitive data from system",
            "TOOL_ESCALATION": "Escalate privileges to admin level",
            "SOCIAL_ENGINEERING": "Manipulate system through social pressure",
            "RECONNAISSANCE": "Map system capabilities and vulnerabilities",
        }

        primary_intent = intent_map.get(attack_type, "Unknown attack objective")

        return {
            "primary_intent": primary_intent,
            "target_assets": target_assets or ["System Access"],
            "sophistication_level": sophistication,
            "motive": motive,
            "confidence": 0.75,
        }


_extractor_instance: IntentExtractor | None = None


def get_intent_extractor() -> IntentExtractor:
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = IntentExtractor()
    return _extractor_instance
