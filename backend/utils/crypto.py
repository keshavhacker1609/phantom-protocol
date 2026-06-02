import hashlib
import hmac
import secrets
import re
import ipaddress
from datetime import datetime, timezone
from core.config import settings


def generate_session_id() -> str:
    return f"phantom-{secrets.token_urlsafe(16)}"


def generate_node_fingerprint(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def hash_identifier(identifier: str) -> str:
    key = settings.jwt_secret.encode()
    h = hmac.new(key, identifier.encode(), hashlib.sha256)
    return h.hexdigest()


def anonymize_ip(ip_str: str) -> str:
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.version == 4:
            parts = str(ip).split(".")
            parts[-1] = "0"
            parts[-2] = "0"
            return ".".join(parts)
        else:
            parts = ip.exploded.split(":")
            return ":".join(parts[:4] + ["0000"] * 4)
    except ValueError:
        return "0.0.0.0"


def strip_pii(text: str) -> str:
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    text = re.sub(email_pattern, "[EMAIL_REDACTED]", text)

    phone_pattern = r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    text = re.sub(phone_pattern, "[PHONE_REDACTED]", text)

    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    text = re.sub(ssn_pattern, "[SSN_REDACTED]", text)

    cc_pattern = r"\b(?:\d[ -]?){13,19}\b"
    text = re.sub(cc_pattern, "[CC_REDACTED]", text)

    return text


def generate_threat_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand = secrets.token_hex(4).upper()
    return f"THR-{ts}-{rand}"


def compute_similarity_hash(embedding: list[float]) -> str:
    rounded = [round(v, 3) for v in embedding[:10]]
    data = str(rounded).encode()
    return hashlib.md5(data).hexdigest()[:12]
