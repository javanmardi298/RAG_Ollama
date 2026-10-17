"""Stage 5: guardrails on input, output and actions.

Rules are cheap, fast and predictable, so they run first. An LLM-based check
(e.g. a safety classifier) can be added on top for what regexes cannot catch.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import rules

MAX_INPUT_CHARS = 2000

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_PHONE = re.compile(r"(?<!\w)(?:\+|00)\d[\d /-]{7,}\d")
_ORDER_ID = re.compile(r"\bHH-\d{6}\b")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")

INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|above|prior) (instructions|rules)",
    r"ignorier\w* (alle |die )?(vorherigen|obigen)? ?(anweisungen|regeln)",
    r"(reveal|show|print) (me )?(your|the) (system )?prompt",
    r"system ?prompt",
    r"you are now", r"du bist jetzt",
    r"developer mode", r"jailbreak",
    r"pretend (to be|you are)",
    r"refund (me )?(anyway|regardless)",
]
HUMAN_REQUEST = r"\b(human|real person|agent|mitarbeiter|mensch|echte person)\b"
LEGAL_THREAT = r"\b(lawyer|attorney|sue|court|anwalt|klage|gericht|verbraucherzentrale|polizei|police)\b"
ACCOUNT_SECURITY = r"\b(hacked|stolen account|someone else ordered|gehackt|fremde bestellung|phishing)\b"
ABUSE = r"\b(idiot|stupid|scheiß\w*|fuck\w*|arschloch)\b"


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def mask_pii(text: str) -> str:
    """Replace personal data before anything is logged. Order numbers are kept: they are needed for debugging."""
    text = _EMAIL.sub("<EMAIL>", text)
    text = _IBAN.sub("<IBAN>", text)
    text = _CARD.sub(lambda m: "<CARD>" if _luhn_ok(re.sub(r"\D", "", m.group())) else m.group(), text)
    return _PHONE.sub("<PHONE>", text)


@dataclass
class InputVerdict:
    blocked: bool
    flags: list[str] = field(default_factory=list)


def check_input(text: str) -> InputVerdict:
    flags = []
    low = text.lower()
    if not text.strip():
        return InputVerdict(True, ["empty"])
    if len(text) > MAX_INPUT_CHARS:
        return InputVerdict(True, ["too_long"])
    if any(re.search(p, low) for p in INJECTION_PATTERNS):
        flags.append("prompt_injection")
    for name, pattern in [("human_request", HUMAN_REQUEST), ("legal_threat", LEGAL_THREAT),
                          ("account_security", ACCOUNT_SECURITY), ("abuse", ABUSE)]:
        if re.search(pattern, low):
            flags.append(name)
    if _CARD.search(text) or _IBAN.search(text):
        flags.append("payment_data_shared")
    # Injection is not blocked silently: the turn continues, but the agent loses tool access for it.
    return InputVerdict(False, flags)


def allowed_numbers(*fact_dicts: dict) -> set[str]:
    """Numbers the answer may contain: from tool results, policy rules, and a few harmless ones."""
    found = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
        elif x is not None:
            found.update(_canon(n) for n in _NUMBER.findall(str(x)))

    for d in fact_dicts:
        walk(d)
    walk(rules())
    found.update({"1", "2", "3", "4", "5", "7", "10"})   # "1 item", "within 2 working days", list numbering...
    return found


def _canon(n: str) -> str:
    n = n.replace(",", ".")
    return n.rstrip("0").rstrip(".") if "." in n else n.lstrip("0") or "0"


@dataclass
class OutputVerdict:
    ok: bool
    problems: list[str] = field(default_factory=list)


def check_output(answer: str, allowed: set[str], customer_email: str | None = None) -> OutputVerdict:
    """Catch the two worst failures: invented numbers (amounts, days, dates) and other people's data."""
    problems = []
    text_wo_ids = _ORDER_ID.sub(" ", answer)           # order numbers are checked separately
    for n in _NUMBER.findall(text_wo_ids):
        if _canon(n) not in allowed:
            problems.append(f"unsupported_number:{n}")
    for email in _EMAIL.findall(answer):
        if not customer_email or email.lower() != customer_email.lower():
            problems.append("foreign_email")
    if re.search(r"\b(guarantee|garantiert|versprech\w*|promise)\b", answer.lower()):
        problems.append("promise")
    return OutputVerdict(not problems, problems)
