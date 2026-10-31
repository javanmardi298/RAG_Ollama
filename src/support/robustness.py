"""Stage 7: German and noisy input.

* detect_language: a tiny stopword-based detector (enough for en/de; swap for fastText lid or lingua for more languages)
* noisify: controlled typo injection, to draw an accuracy-vs-noise curve
* translate_batch: LLM translation of test messages, to be spot-checked by a person
"""
from __future__ import annotations

import random
import re

_DE = set("ich du sie wir mein meine meinen bitte nicht und ist die der das den dem ein eine einen wo wann "
          "warum wie habe hat bestellung lieferung rücksendung erstattung paket stornieren noch schon kann "
          "möchte würde danke hallo mit für auf zu".split())
_EN = set("i you we my please not and is the a an where when why how have has order delivery return refund "
          "package cancel still already can would want thanks hello with for on to".split())
_WORD = re.compile(r"[a-zA-ZäöüÄÖÜß]+")


def detect_language(text: str, min_hits: int = 2) -> str | None:
    words = [w.lower() for w in _WORD.findall(text)]
    if any(ch in text for ch in "äöüß"):
        return "de"
    de, en = sum(w in _DE for w in words), sum(w in _EN for w in words)
    if max(de, en) < min_hits or de == en:
        return None
    return "de" if de > en else "en"


# QWERTZ/QWERTY neighbours for realistic substitutions
_NEIGHBOURS = {
    "a": "qsy", "b": "vgn", "c": "xdv", "d": "sfe", "e": "wrd", "f": "dgr", "g": "fht", "h": "gjz",
    "i": "uok", "j": "hku", "k": "jli", "l": "kop", "m": "nk", "n": "bm", "o": "ipl", "p": "ol",
    "q": "wa", "r": "eft", "s": "adw", "t": "rgz", "u": "zij", "v": "cb", "w": "qse", "x": "ycs",
    "y": "xa", "z": "tuh",
}


def add_typos(text: str, rate: float, rng: random.Random) -> str:
    """Each letter is corrupted with probability `rate` by one of four edit types."""
    out = []
    chars = list(text)
    i = 0
    while i < len(chars):
        ch = chars[i]
        if ch.isalpha() and rng.random() < rate:
            kind = rng.choice(["swap", "drop", "double", "neighbour"])
            if kind == "swap" and i + 1 < len(chars):
                out += [chars[i + 1], ch]
                i += 2
                continue
            if kind == "drop":
                i += 1
                continue
            if kind == "double":
                out += [ch, ch]
            else:
                near = _NEIGHBOURS.get(ch.lower())
                out.append(rng.choice(near) if near else ch)
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def noisify(text: str, level: int, seed: int = 0) -> str:
    """Level 0 = clean ... 3 = very noisy. Same text + level + seed -> same output."""
    rng = random.Random(f"{seed}:{level}:{text}")
    if level == 0:
        return text
    if level >= 2:
        text = re.sub(r"[?.!,]", "", text).lower()
    if level >= 3:
        text = re.sub(r"\b(please|bitte)\b ?", "", text, flags=re.I).strip()
    return add_typos(text, rate=[0, 0.03, 0.07, 0.12][level], rng=rng)


TRANSLATE_SCHEMA = {"type": "object", "properties": {"translations": {"type": "array", "items": {"type": "string"}}},
                    "required": ["translations"]}


def translate_batch(llm, texts: list[str], target: str = "German") -> list[str]:
    """Translate customer messages with an LLM, keeping placeholders like {{Order Number}} unchanged.

    Machine translation is too clean and too formal compared with real German customers:
    check a sample by hand and also write some messages yourself.
    """
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(texts))
    prompt = (f"Translate these customer-support messages into natural, informal {target} as a real customer "
              f"would write them. Keep {{{{...}}}} placeholders and order numbers unchanged. "
              f"Return exactly {len(texts)} translations in order.\n\n{numbered}")
    result = llm.json([{"role": "user", "content": prompt}], TRANSLATE_SCHEMA)["translations"]
    if len(result) != len(texts):
        raise ValueError(f"expected {len(texts)} translations, got {len(result)}")
    return result
