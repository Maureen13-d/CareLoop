"""Text helpers shared by the safety rules and the Lite matcher.

Messages are normalised so that "I can't afford it!!" and "i cant afford it" look the same."""
import re

NEGATIONS = {"not", "no", "never", "dont", "cant", "cannot", "isnt", "wasnt", "wont", "didnt", "without", "neither", "nor"}

# Common SMS shorthand. Extend freely; keep entries lowercase.
SMS_SHORTHAND = {
    "u": "you", "ur": "your", "pls": "please", "plz": "please", "abt": "about", "wat": "what", "wht": "what",
    "r": "are", "hosp": "hospital", "msg": "message", "dnt": "dont", "cnt": "cant", "im": "i am", "ive": "i have",
    "idk": "i do not know", "thx": "thanks", "gonna": "going to",
}


def normalise(text: str | None) -> str:
    t = (text or "").lower().replace("\u2019", "'").replace("`", "'")
    t = t.replace("'", "")                    # don't -> dont, can't -> cant
    t = re.sub(r"[^a-z0-9\s]", " ", t)        # punctuation becomes spaces
    words = [SMS_SHORTHAND.get(w, w) for w in t.split()]
    return " ".join(words)


def tokens(norm: str) -> list[str]:
    return norm.split()


def phrase_positions(toks: list[str], phrase: str) -> list[int]:
    """Start positions where the (already normalised) phrase occurs in the token list."""
    p = phrase.split()
    if not p:
        return []
    return [i for i in range(len(toks) - len(p) + 1) if toks[i:i + len(p)] == p]


def is_negated(toks: list[str], start: int, window: int) -> bool:
    return any(t in NEGATIONS for t in toks[max(0, start - window):start])
