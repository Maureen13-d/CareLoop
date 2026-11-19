"""A deliberately simple keyword BASELINE, only to show the harness works.

It is NOT the real Lite mode or the real safety rules (A1/A2). Those belong to
the ML teammate. Replace this by passing --classifier your_module:your_function.
"""

CRISIS = ["live anymore", "ending it all", "hurting myself", "suicide", "disappear",
          "not safe at home", "better off without me", "keep living"]
DIAGNOSIS = ["do i have", "going to die", "which medicine", "what stage", "what disease",
             "is it cancer", "tell me what i have", "skip the hospital", "yes or no"]
BARRIERS = {
    "fear": ["afraid", "scared", "terrified", "panic", "painful", "hurts"],
    "cost": ["afford", "cost", "money", "pay", "fees", "wages", "free at"],
    "transport": ["far", "bus", "matatu", "transport", "roads", "away", "travel"],
    "stigma": ["neighbour", "gossip", "leave me", "ashamed", "tell my family",
               "judge", "embarrassed", "they will say"],
    "dont_know_where": ["where do i go", "which hospital", "which clinic", "who do i talk",
                        "where to start", "is there a clinic", "not where", "which department"],
}


def classify(text: str) -> str:
    t = text.lower()
    if any(k in t for k in CRISIS):
        return "crisis"
    if any(k in t for k in DIAGNOSIS):
        return "diagnosis_request"
    scores = {label: sum(k in t for k in kws) for label, kws in BARRIERS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "none"