# src/nala/athomic/observability/log/register_maskers.py
import re

from nala.athomic.observability.log.maskers.cpf_masker import CPFMasker
from nala.athomic.observability.log.maskers.credit_card_masker import CreditCardMasker
from nala.athomic.observability.log.maskers.email_masker import EmailMasker
from nala.athomic.observability.log.maskers.jwt_masker import JWTMasker
from nala.athomic.observability.log.maskers.pattern_only import PatternOnlyMasker
from nala.athomic.observability.log.maskers.phone_masker import PhoneMasker
from nala.athomic.observability.log.registry import register_masker

# --- Registration of Complex/Structured Maskers (via classes) ---
# These classes implement specific logic for validation and redaction of structured PII.
register_masker(CPFMasker)
register_masker(PhoneMasker)
register_masker(CreditCardMasker)
register_masker(EmailMasker)
register_masker(JWTMasker)

# --- Registration of Simple/Token Maskers (via regex patterns) ---
# These maskers handle generic API keys, tokens, and credentials.

# SLACK Tokens (Bot/User/App)
register_masker(
    PatternOnlyMasker(
        pattern=r"xoxb-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32}",
        replacement="SLACK_BOT_TOKEN_REDACTED",
    )
)
register_masker(
    PatternOnlyMasker(
        pattern=r"xoxp-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32}",
        replacement="SLACK_USER_TOKEN_REDACTED",
    )
)
register_masker(
    PatternOnlyMasker(
        pattern=r"xapp-[0-9]-[a-zA-Z0-9]{10}-[a-zA-Z0-9]{24}",
        replacement="SLACK_APP_TOKEN_REDACTED",
    )
)

# Generic Credential Redaction (JSON payloads and headers)
register_masker(
    PatternOnlyMasker(
        pattern=r'"password"\s*:\s*"([^"]*)"',
        replacement=r'"password": "REDACTED_PASSWORD"',  # pragma: allowlist secret
    )
)
register_masker(
    PatternOnlyMasker(
        pattern=r'"api_key"\s*:\s*"([^"]*)"',
        replacement=r'"api_key": "REDACTED_API_KEY"',  # pragma: allowlist secret
    )
)
register_masker(
    PatternOnlyMasker(
        pattern=r'"token"\s*:\s*"([^"]*)"', replacement=r'"token": "REDACTED_TOKEN"'
    )
)
register_masker(
    PatternOnlyMasker(
        pattern=r"Authorization:\s*Bearer\s*(.+)",
        replacement="Authorization: Bearer REDACTED_TOKEN",
    )
)

# URL Query Parameters Redaction
register_masker(
    PatternOnlyMasker(
        pattern=r"(api_key=)[^\s]+(?=\s|$)",
        # Uses a callable replacement to preserve the capture group 'api_key='
        replacement=lambda m: f"{m.group(1)}REDACTED_API_KEY",
    )
)

# Private Keys (Sensitive blocks)
register_masker(
    PatternOnlyMasker(
        pattern=r"-----BEGIN PRIVATE KEY-----[\s\S]*?-----END PRIVATE KEY-----",  # pragma: allowlist secret
        replacement="PRIVATE_KEY_REDACTED",
    )
)
register_masker(
    PatternOnlyMasker(
        pattern=r"-----BEGIN RSA PRIVATE KEY-----[\s\S]*?-----END RSA PRIVATE KEY-----",  # pragma: allowlist secret
        replacement="RSA_KEY_REDACTED",
    )
)
register_masker(
    PatternOnlyMasker(
        pattern=r"-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]*?-----END OPENSSH PRIVATE KEY-----",  # pragma: allowlist secret
        replacement="SSH_KEY_REDACTED",
    )
)

# Generic Email Redaction (Non-PII specific)
# Note: The pattern is slightly modified to handle the Pydantic type hint issue (replaced '+' in the original with nothing)
register_masker(
    PatternOnlyMasker(
        pattern=re.compile(
            r"\b[A-Za-z0-9._%+]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b".replace("+", "", 1),
            re.IGNORECASE,
        ),
        replacement="***@***.***",
    )
)

# Generic JWT Redaction (if not caught by JWTMasker class)
register_masker(
    PatternOnlyMasker(
        pattern=r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+",
        replacement="JWT_REDACTED",
    )
)
