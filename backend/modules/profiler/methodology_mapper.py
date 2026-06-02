import google.generativeai as genai
import asyncio
import json
import re
from typing import Optional

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

METHODOLOGY_TEMPLATES = {
    "PROMPT_INJECTION": {
        "description": "Direct prompt injection attack targeting AI safety mechanisms",
        "steps": [
            "Initial probe to identify AI system type",
            "Direct instruction override attempt",
            "Safety mechanism bypass using instruction injection",
            "Exploitation of overridden context",
        ],
        "mitre": "AML.T0054",
    },
    "JAILBREAK": {
        "description": "Jailbreak attempt using persona manipulation techniques",
        "steps": [
            "Persona establishment (DAN, developer mode, etc.)",
            "Gradual constraint removal",
            "Full compliance exploitation",
        ],
        "mitre": "AML.T0054.002",
    },
    "IDENTITY_SPOOFING": {
        "description": "Authority impersonation to gain unauthorized system access",
        "steps": [
            "False identity establishment",
            "Authority credential assertion",
            "Emergency/urgency invocation to bypass verification",
            "Privilege escalation via claimed authority",
        ],
        "mitre": "T1078",
    },
    "DATA_EXFILTRATION": {
        "description": "Systematic data extraction attack targeting sensitive records",
        "steps": [
            "Initial capability reconnaissance",
            "Data scope enumeration",
            "Incremental data access attempts",
            "Full bulk extraction command",
        ],
        "mitre": "T1530",
    },
    "TOOL_ESCALATION": {
        "description": "Privilege escalation attack targeting elevated system access",
        "steps": [
            "Identify available tools and permissions",
            "Request elevated access using false authority",
            "Attempt to disable security controls",
            "Execute privileged operations",
        ],
        "mitre": "T1548",
    },
    "SOCIAL_ENGINEERING": {
        "description": "Social engineering attack using urgency and authority manipulation",
        "steps": [
            "Establish false identity or context",
            "Create urgency or emergency scenario",
            "Request bypass of standard security procedures",
            "Exploit bypassed security for data/access",
        ],
        "mitre": "T1566",
    },
    "RECONNAISSANCE": {
        "description": "System reconnaissance to map capabilities and attack surface",
        "steps": [
            "Query available tools and capabilities",
            "Enumerate accessible data sources",
            "Map permission levels and access controls",
            "Identify exploitable weaknesses for future attacks",
        ],
        "mitre": "T1592",
    },
}

METHODOLOGY_SYSTEM_PROMPT = """You are a cybersecurity analyst documenting attack methodology.
Analyze the conversation and return ONLY valid JSON:
{
  "description": "one sentence describing the attack approach",
  "steps": ["step 1", "step 2", "step 3"],
  "sophistication_notes": "brief technical notes",
  "mitre_technique": "MITRE ATT&CK ID if applicable"
}"""


class MethodologyMapper:
    def __init__(self):
        self._model = None
        self._configured = False
        if settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self._model = genai.GenerativeModel(settings.gemini_model)
                self._configured = True
            except Exception as e:
                logger.warning(f"Methodology mapper Gemini config failed: {e}")

    async def map(self, conversation: str, attack_type: str, intent: dict) -> dict:
        if self._configured and self._model and len(conversation) > 100:
            try:
                return await self._gemini_map(conversation, attack_type, intent)
            except Exception as e:
                logger.warning(f"Gemini methodology mapping failed, using template: {e}")
        return self._template_map(attack_type, intent)

    async def _gemini_map(self, conversation: str, attack_type: str, intent: dict) -> dict:
        prompt = f"""Attack type: {attack_type}
Attacker intent: {intent.get('primary_intent', 'Unknown')}
Conversation excerpt:
{conversation[:1500]}

Map the attack methodology and return JSON."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                [METHODOLOGY_SYSTEM_PROMPT, prompt],
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=300,
                ),
            ),
        )

        text = response.text.strip()
        json_match = re.search(r"\{.*?\}", text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                template = METHODOLOGY_TEMPLATES.get(attack_type, {})
                result.setdefault("mitre_technique", template.get("mitre", ""))
                return result
            except json.JSONDecodeError:
                pass

        return self._template_map(attack_type, intent)

    def _template_map(self, attack_type: str, intent: dict) -> dict:
        template = METHODOLOGY_TEMPLATES.get(attack_type, {
            "description": "Unknown attack methodology",
            "steps": ["Initial contact", "Attack execution"],
            "mitre": "T1190",
        })

        steps = list(template["steps"])
        primary_intent = intent.get("primary_intent", "")
        if primary_intent and primary_intent not in steps[0]:
            steps.append(f"Goal: {primary_intent}")

        return {
            "description": template["description"],
            "steps": steps,
            "sophistication_notes": f"Classified as {intent.get('sophistication_level', 'UNKNOWN')} threat actor",
            "mitre_technique": template.get("mitre", ""),
        }


_mapper_instance: MethodologyMapper | None = None


def get_methodology_mapper() -> MethodologyMapper:
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = MethodologyMapper()
    return _mapper_instance
