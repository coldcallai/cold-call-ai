"""
UniversalBrain Contract — Jargon translation utility.

Behavior owned by UniversalBrain; lexicon owned by Playbook.

Rule (PRD): "Agent speaks business owner, not merchant services."
If a caller asks "What do you mean?" within N seconds of the AI's last
utterance, the engine flags the last phrase as suspected jargon and
substitutes the playbook-supplied plain-English version on the next attempt.
"""
from __future__ import annotations
from typing import Optional


class JargonChecker:
    def __init__(self, jargon_map: dict[str, str]) -> None:
        # Normalize keys to lowercase for case-insensitive matching.
        self._map = {k.lower(): v for k, v in (jargon_map or {}).items()}

    def find_jargon(self, text: str) -> list[str]:
        """Return any jargon phrases present in `text`."""
        t = (text or "").lower()
        return [j for j in self._map if j in t]

    def plain_english(self, jargon: str) -> Optional[str]:
        return self._map.get(jargon.lower())

    def translate(self, text: str) -> str:
        """Replace jargon substrings with plain-English equivalents."""
        out = text
        # process longest keys first to avoid partial overlaps
        for j in sorted(self._map.keys(), key=len, reverse=True):
            if j in out.lower():
                # case-preserving simple replace at lowered match position
                lower = out.lower()
                idx = lower.find(j)
                while idx != -1:
                    out = out[:idx] + self._map[j] + out[idx + len(j):]
                    lower = out.lower()
                    idx = lower.find(j, idx + len(self._map[j]))
        return out
