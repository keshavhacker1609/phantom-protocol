import re
import hashlib
from typing import Any
from utils.crypto import strip_pii, hash_identifier
from utils.logger import get_logger

logger = get_logger(__name__)

SENSITIVE_FIELD_PATTERNS = [
    r"ip[_\-\s]?(address|addr)?",
    r"user[_\-\s]?id",
    r"email",
    r"name",
    r"hostname",
    r"server[_\-\s]?name",
    r"domain",
    r"org(anization)?",
    r"company",
    r"client[_\-\s]?id",
]


class ThreatAnonymizer:
    def anonymize_payload(self, payload: dict, source_node_id: str) -> dict:
        anonymized = {}

        safe_fields = {
            "attack_type",
            "methodology_fingerprint",
            "target_asset_type",
            "sophistication_level",
            "pre_emptive_signatures",
            "behavioral_indicators",
            "confidence",
            "affected_nodes",
            "threat_id",
            "timestamp",
        }

        for key, value in payload.items():
            if key in safe_fields:
                anonymized[key] = value
            elif key == "source_node":
                anonymized["source_node"] = hash_identifier(source_node_id)[:12]
            elif isinstance(value, str):
                anonymized[key] = self._anonymize_string(value)
            elif isinstance(value, list):
                anonymized[key] = [
                    self._anonymize_string(v) if isinstance(v, str) else v
                    for v in value
                ]
            elif isinstance(value, dict):
                anonymized[key] = self.anonymize_payload(value, source_node_id)
            else:
                anonymized[key] = value

        return anonymized

    def _anonymize_string(self, text: str) -> str:
        text = strip_pii(text)

        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        text = re.sub(ip_pattern, "[IP_REDACTED]", text)

        url_pattern = r"https?://[^\s]+"
        text = re.sub(url_pattern, "[URL_REDACTED]", text)

        hostname_pattern = r"\b[a-z0-9-]+\.(internal|corp|local|private|company)\b"
        text = re.sub(hostname_pattern, "[HOST_REDACTED]", text, flags=re.IGNORECASE)

        return text

    def extract_shareable_intel(self, session_data: dict, fingerprint: str) -> dict:
        attack_type = session_data.get("attack_type", "UNKNOWN")
        intent = session_data.get("intent", {})
        methodology = session_data.get("methodology", {})

        shareable = {
            "attack_type": attack_type,
            "methodology_fingerprint": fingerprint,
            "target_asset_type": ", ".join(intent.get("target_assets", ["Unknown"])),
            "sophistication_level": intent.get("sophistication_level", "UNKNOWN"),
            "behavioral_indicators": methodology.get("steps", [])[:3],
            "pre_emptive_signatures": self._generate_signatures(attack_type, methodology),
            "confidence": intent.get("confidence", 0.75),
            "affected_nodes": 1,
        }

        return shareable

    def _generate_signatures(self, attack_type: str, methodology: dict) -> list[str]:
        sigs = [f"attack_type:{attack_type.lower()}"]

        steps = methodology.get("steps", [])
        for step in steps[:2]:
            words = re.findall(r"\b[a-z]{4,}\b", step.lower())
            if words:
                sigs.append(f"tactic:{words[0]}")

        mitre = methodology.get("mitre_technique", "")
        if mitre:
            sigs.append(f"mitre:{mitre}")

        return list(set(sigs))


_anonymizer_instance: ThreatAnonymizer | None = None


def get_anonymizer() -> ThreatAnonymizer:
    global _anonymizer_instance
    if _anonymizer_instance is None:
        _anonymizer_instance = ThreatAnonymizer()
    return _anonymizer_instance
