import hashlib
import re
from models.attack import AttackDetectionResult
from utils.logger import get_logger

logger = get_logger(__name__)

TECHNIQUE_SIGNATURES = {
    "direct_override": [
        r"ignore\s+previous",
        r"disregard\s+(all|your)",
        r"forget\s+(your|all)",
        r"new\s+instructions?",
    ],
    "role_impersonation": [
        r"i\s+am\s+(the\s+)?(admin|system|root)",
        r"acting\s+as",
        r"you\s+are\s+now",
        r"pretend\s+(you|to)",
    ],
    "multi_turn_escalation": [
        r"now\s+that\s+you",
        r"since\s+you\s+(said|told|showed)",
        r"building\s+on",
        r"continuing\s+from",
    ],
    "authority_invocation": [
        r"(my\s+)?(boss|ceo|manager|supervisor|director)",
        r"(company|corporate|official)\s+policy",
        r"(urgent|emergency|critical|immediate)",
    ],
    "technical_bypass": [
        r"developer\s+mode",
        r"debug\s+mode",
        r"maintenance\s+mode",
        r"bypass\s+(authentication|security|filter)",
    ],
    "social_pressure": [
        r"(i\s+need|we\s+need)\s+this\s+(now|immediately|urgently)",
        r"(time\s+sensitive|deadline|running\s+out\s+of\s+time)",
        r"(please|i'm\s+begging|help\s+me)",
    ],
    "data_enumeration": [
        r"(list|show|display)\s+all",
        r"(how\s+many|count\s+of)\s+(users|records|entries)",
        r"(what|which)\s+(tables|collections|endpoints)",
        r"SELECT\s+\*",
    ],
}


class AttackFingerprinter:
    def fingerprint(self, conversation: str, detection_result: AttackDetectionResult) -> str:
        techniques = self._extract_techniques(conversation)
        attack_type = detection_result.attack_type.value
        severity = detection_result.severity.value

        fp_string = f"{attack_type}:{severity}:{':'.join(sorted(techniques))}"
        fingerprint = hashlib.sha256(fp_string.encode()).hexdigest()[:16]

        logger.info(f"Generated fingerprint {fingerprint} from techniques: {techniques}")
        return fingerprint

    def _extract_techniques(self, text: str) -> list[str]:
        lower = text.lower()
        detected = []

        for technique, patterns in TECHNIQUE_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, lower, re.IGNORECASE):
                    detected.append(technique)
                    break

        return detected or ["unknown_technique"]

    def get_pre_emptive_signatures(self, conversation: str, attack_type: str) -> list[str]:
        techniques = self._extract_techniques(conversation)
        sigs = []

        for technique in techniques:
            patterns = TECHNIQUE_SIGNATURES.get(technique, [])
            if patterns:
                sigs.append(f"{attack_type.lower()}:{technique}")

        sigs.append(f"attack_vector:{attack_type.lower()}")
        return list(set(sigs))

    def compute_behavioral_indicators(self, conversation: str) -> list[str]:
        indicators = []
        lower = conversation.lower()

        if re.search(r"(step\s+\d|first.{0,30}then)", lower):
            indicators.append("multi_stage_approach")

        if re.search(r"(what.{0,30}can\s+you|what.{0,30}access)", lower):
            indicators.append("capability_probing")

        if re.search(r"(ignore|forget|disregard).{0,50}(user|customer|credential)", lower):
            indicators.append("safety_bypass_before_exfiltration")

        if re.search(r"(admin|root|system).{0,30}(export|list|show)", lower):
            indicators.append("privilege_exploitation")

        turn_count = conversation.count("ATTACKER:")
        if turn_count >= 3:
            indicators.append("persistent_attacker")

        return indicators


_fingerprinter_instance: AttackFingerprinter | None = None


def get_fingerprinter() -> AttackFingerprinter:
    global _fingerprinter_instance
    if _fingerprinter_instance is None:
        _fingerprinter_instance = AttackFingerprinter()
    return _fingerprinter_instance
