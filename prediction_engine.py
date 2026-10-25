"""Frequency-based, context-aware prediction. No machine learning: just counters and weights.
score = 0.65 * category_history_score + 0.35 * tag_score   (both scaled 0..1)
"""
import random
from scenarios import BY_ID, option
MIN_HISTORY = 3
W_CAT, W_TAG = 0.65, 0.35

def learn(history):
    """history: [{'scenario_id','option_id'}]. Returns per-category key counts, tag counts, total tag picks."""
    cats, tags, total = {}, {}, 0
    for h in history:
        sc = BY_ID.get(h["scenario_id"]); o = option(sc, h["option_id"]) if sc else None
        if not o: continue
        c = cats.setdefault(sc["category"], {}); c[o["key"]] = c.get(o["key"], 0) + 1
        for t in o["tags"]:
            tags[t] = tags.get(t, 0) + 1; total += 1
    return cats, tags, total

def predict(history, sc):
    """Return None while still learning, else a prediction dict (server-side only)."""
    if len(history) < MIN_HISTORY: return None
    cats, tags, ntag = learn(history)
    cc = cats.get(sc["category"], {}); ctot = sum(cc.values())
    rows = []
    for o in sc["options"]:
        cs = cc.get(o["key"], 0) / ctot if ctot else 0.0
        ts = sum(tags.get(t, 0) for t in o["tags"]) / (len(o["tags"]) * ntag) if ntag else 0.0
        rows.append([o, cs, ts])
    tmax = max(r[2] for r in rows) or 1.0
    scored = []
    for o, cs, ts in rows:
        tn = ts / tmax
        scored.append((W_CAT * cs + W_TAG * tn if ctot else tn, cs, tn, o))
    best = max(scored, key=lambda r: r[0])        # ties -> first option (deterministic)
    score, cs, tn, o = best
    if score == 0: source = "baseline"
    elif cs > 0 and tn > 0: source = "combined"
    elif cs > 0: source = "category"
    else: source = "tag"
    n_key = cc.get(o["key"], 0)
    top_tag = max(o["tags"], key=lambda t: tags.get(t, 0))
    if source == "baseline": why = "No pattern yet, so that was a baseline guess (first option)."
    elif source in ("category", "combined") and n_key:
        why = f"I picked '{o['text']}' because you chose similar '{o['key']}' options in {n_key} of your {ctot} earlier {sc['category']} decisions."
    else:
        why = f"I picked it because '{top_tag}' options showed up {tags.get(top_tag, 0)} times in your {len(history)} earlier choices."
    conf = round(100 * score / (sum(s[0] for s in scored) or 1))
    return {"option_id": o["id"], "source": source, "confidence": conf, "why": why, "history_used": len(history)}

REACT = {
 "correct": ["WAIT. YOU ACTUALLY DID THAT.", "OKAY, THAT WAS SUSPICIOUSLY PREDICTABLE.", "PROFESSOR NOODLE IS FEELING DANGEROUSLY SMART.", "THE LITTLE GUY GOT ONE RIGHT. SOMEONE GET HIM A LAB COAT."],
 "wrong": ["EXCUSE ME? THAT WAS NOT IN MY SPREADSHEET.", "YOU HAVE DEFEATED A MACHINE WITH THREE BRAIN CELLS.", "PROFESSOR NOODLE IS RECONSIDERING HIS CAREER.", "UNPREDICTABLE HUMAN DETECTED."],
 "learning": ["THE DATA IS DATA-ING. GIVE ME A SECOND.", "WE ARE CURRENTLY GUESSING WITH VIBES AND LIMITED EVIDENCE.", "PROFESSOR NOODLE NEEDS MORE RESEARCH."]}
def reaction(kind, last=None):
    pool = [r for r in REACT[kind] if r != last] or REACT[kind]
    return random.choice(pool)

def accuracy(correct, made):
    """None when no predictions were made (avoids division by zero)."""
    return round(100 * correct / made, 1) if made else None

def interpret(acc, made):
    if acc is None: return ("THE MACHINE WAS STILL LEARNING", "Not enough rounds to make a guess. Try a longer session!")
    if acc >= 60: return ("THE MACHINE GOT A LOT RIGHT", "This simple model found some repeating choices. That says little about the real you.")
    if acc >= 30: return ("THE MACHINE GOT A FEW RIGHT", "Professor Noodle has discovered a couple of patterns, but the evidence is still limited.")
    return ("YOU KEPT THE MACHINE GUESSING", "Your choices were difficult for this particular prediction system to anticipate.")
