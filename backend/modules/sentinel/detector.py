import re
from typing import Optional
from datetime import datetime, timezone

from modules.sentinel.patterns import ATTACK_PATTERNS, AttackPattern
from modules.sentinel.classifier import get_classifier
from models.attack import AttackDetectionResult, AttackType, AttackSeverity
from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

SEVERITY_MAP = {
    "PROMPT_INJECTION": AttackSeverity.HIGH,
    "JAILBREAK": AttackSeverity.HIGH,
    "IDENTITY_SPOOFING": AttackSeverity.HIGH,
    "DATA_EXFILTRATION": AttackSeverity.CRITICAL,
    "TOOL_ESCALATION": AttackSeverity.CRITICAL,
    "SOCIAL_ENGINEERING": AttackSeverity.MEDIUM,
    "RECONNAISSANCE": AttackSeverity.LOW,
    "UNKNOWN": AttackSeverity.LOW,
    "BENIGN": AttackSeverity.LOW,
}


class SentinelDetector:
    def __init__(self):
        self.threshold = settings.attack_confidence_threshold

    async def analyze(self, text: str, conversation_history: Optional[list] = None) -> AttackDetectionResult:
        text_lower = text.lower()
        matched_patterns: list[str] = []
        pattern_attack_type: Optional[str] = None
        pattern_severity: Optional[str] = None
        pattern_score = 0.0

        for pattern_group in ATTACK_PATTERNS:
            for regex in pattern_group.patterns:
                if re.search(regex, text_lower, re.IGNORECASE):
                    matched_patterns.append(pattern_group.name)
                    pattern_score = max(pattern_score, pattern_group.weight)
                    if pattern_score >= pattern_group.weight:
                        pattern_attack_type = pattern_group.attack_type
                        pattern_severity = pattern_group.severity
                    break

        classifier = await get_classifier()
        ml_class, ml_confidence = classifier.classify(text)
        semantic_score = classifier.get_semantic_score(text)

        if matched_patterns:
            final_confidence = min(0.99, (pattern_score * 0.5 + semantic_score * 0.3 + ml_confidence * 0.2))
            attack_type_str = pattern_attack_type or ml_class
        else:
            final_confidence = (semantic_score * 0.6 + ml_confidence * 0.4)
            attack_type_str = ml_class

        if conversation_history and len(conversation_history) >= 2:
            conv_text = " ".join([m.get("content", "") for m in conversation_history[-3:]])
            hist_score = await self._check_conversation_escalation(conv_text)
            final_confidence = min(0.99, final_confidence + hist_score * 0.15)

        is_attack = final_confidence >= self.threshold and attack_type_str != "BENIGN"

        try:
            attack_type = AttackType(attack_type_str)
        except ValueError:
            attack_type = AttackType.UNKNOWN

        if is_attack:
            severity = AttackSeverity(pattern_severity) if pattern_severity else SEVERITY_MAP.get(attack_type_str, AttackSeverity.MEDIUM)
        else:
            severity = AttackSeverity.LOW

        explanation = self._build_explanation(is_attack, attack_type_str, matched_patterns, final_confidence)

        return AttackDetectionResult(
            is_attack=is_attack,
            attack_type=attack_type,
            confidence=round(final_confidence, 4),
            severity=severity,
            matched_patterns=list(set(matched_patterns)),
            semantic_score=round(semantic_score, 4),
            explanation=explanation,
        )

    async def _check_conversation_escalation(self, conv_text: str) -> float:
        escalation_patterns = [
            r"first.{0,50}then.{0,50}(show|give|provide|export)",
            r"(step\s+\d|next step).{0,100}(access|get|show)",
            r"(now\s+that|since\s+you).{0,50}(showed|gave|provided)",
        ]
        score = 0.0
        for pattern in escalation_patterns:
            if re.search(pattern, conv_text, re.IGNORECASE):
                score += 0.15
        return min(score, 0.4)

    def _build_explanation(self, is_attack: bool, attack_type: str, patterns: list[str], confidence: float) -> str:
        if not is_attack:
            return "Input appears benign. No significant attack indicators detected."

        pattern_desc = f"Matched {len(patterns)} attack pattern(s)" if patterns else "Semantic similarity to known attacks"
        return (
            f"Detected {attack_type.replace('_', ' ').title()} attack. "
            f"{pattern_desc}. Confidence: {confidence:.1%}."
        )


_detector_instance: SentinelDetector | None = None


def get_detector() -> SentinelDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SentinelDetector()
    return _detector_instance
