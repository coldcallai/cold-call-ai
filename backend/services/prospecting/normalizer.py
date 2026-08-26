"""Phase 1 — Normalization. Pure functions, no I/O."""
from __future__ import annotations
import re
from urllib.parse import urlparse


# Suffixes stripped from business names for fuzzy matching
NAME_SUFFIXES = (
    "llc", "l.l.c.", "inc", "inc.", "corp", "corporation", "co", "company",
    "center", "centre", "group", "associates", "assoc", "pllc", "pc", "p.c.",
    "pa", "p.a.", "dds", "d.d.s.", "md", "m.d.", "dvm",
)

STREET_ABBREVIATIONS = {
    "street": "st", "road": "rd", "avenue": "ave", "boulevard": "blvd",
    "drive": "dr", "lane": "ln", "court": "ct", "place": "pl",
    "highway": "hwy", "parkway": "pkwy", "circle": "cir", "terrace": "ter",
    "suite": "ste", "north": "n", "south": "s", "east": "e", "west": "w",
    "northwest": "nw", "northeast": "ne", "southwest": "sw", "southeast": "se",
}


def normalize_website(url: str | None) -> str | None:
    """https://www.example.com/path?x=1 -> example.com"""
    if not url:
        return None
    u = url.strip().lower()
    if "://" not in u:
        u = "https://" + u
    try:
        host = urlparse(u).hostname or ""
    except Exception:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host or None


def normalize_phone(phone: str | None) -> str | None:
    """(404) 555-1212 / +1-404-555-1212 -> 4045551212"""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 else None


def normalize_address(address: str | None) -> str | None:
    """620 Peachtree Road, Suite 200 -> 620 peachtree rd ste 200"""
    if not address:
        return None
    a = address.lower().strip()
    a = re.sub(r"[.,#]", " ", a)
    a = re.sub(r"\s+", " ", a)
    tokens = a.split()
    out = [STREET_ABBREVIATIONS.get(t, t) for t in tokens]
    return " ".join(out).strip() or None


def normalize_name(name: str | None) -> str | None:
    """Atlanta Dental Center LLC -> atlanta dental"""
    if not name:
        return None
    n = name.lower().strip()
    n = re.sub(r"[.,&]", " ", n)
    n = re.sub(r"\s+", " ", n)
    tokens = n.split()
    # strip trailing suffix tokens
    while tokens and tokens[-1] in NAME_SUFFIXES:
        tokens.pop()
    # also drop interior suffix-like tokens
    tokens = [t for t in tokens if t not in NAME_SUFFIXES]
    return " ".join(tokens).strip() or None
