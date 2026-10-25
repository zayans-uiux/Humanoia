"""Flask routes. Prediction logic lives in prediction_engine.py."""
import json, re, uuid, random
from flask import Flask, jsonify, request, render_template
import database as db, prediction_engine as eng
from scenarios import SCENARIOS, BY_ID, option, public

app = Flask(__name__)
TOKEN_RE = re.compile(r"^[A-Za-z0-9\-]{8,64}$")
def err(msg, code=400): return jsonify(error=msg), code
def body():
    d = request.get_json(silent=True); return d if isinstance(d, dict) else {}

def get_player(c, token, nickname=None):
    if not isinstance(token, str) or not TOKEN_RE.match(token): return None
    row = c.execute("SELECT * FROM players WHERE token=?", (token,)).fetchone()
    if not row and nickname is not None:
        c.execute("INSERT INTO players(token,nickname) VALUES(?,?)", (token, nickname))
        row = c.execute("SELECT * FROM players WHERE token=?", (token,)).fetchone()
    elif row and nickname:
        c.execute("UPDATE players SET nickname=? WHERE id=?", (nickname, row["id"])); 
    return row

def history(c, pid):
    return [dict(r) for r in c.execute("""SELECT a.scenario_id, a.selected_option_id AS option_id FROM scenario_answers a
        JOIN game_sessions s ON s.id=a.session_id WHERE s.player_id=? ORDER BY a.id""", (pid,))]

def serve_round(c, sid, pid, order, idx):
    sc = BY_ID[order[idx]]
    pred = eng.predict(history(c, pid), sc)
    pending = {"scenario_id": sc["id"], "prediction": pred}
    c.execute("UPDATE game_sessions SET pending_json=? WHERE id=?", (json.dumps(pending), sid))
    shown = {"option_id": pred["option_id"], "source": pred["source"], "confidence": pred["confidence"]} if pred else None
    return {"scenario": public(sc), "round": idx + 1, "prediction": shown}

@app.route("/")
def index(): return render_template("index.html")

@app.get("/api/scenarios")
def scenarios(): return jsonify([public(s) for s in SCENARIOS])

@app.post("/api/game/start")
def start():
    d = body(); nick = str(d.get("nickname") or "").strip()[:24] or "Mystery Human"
    rounds = d.get("rounds", 10)
    if rounds not in (5, 10, 15): return err("rounds must be 5, 10 or 15")
    ids = [s["id"] for s in SCENARIOS]; random.shuffle(ids)
    second = ids[:]; random.shuffle(second)
    order = (ids + second)[:rounds]
    with db.conn() as c:
        p = get_player(c, d.get("token"), nick)
        if not p: return err("invalid player token")
        sid = uuid.uuid4().hex
        c.execute("INSERT INTO game_sessions(id,player_id,rounds_planned,order_json) VALUES(?,?,?,?)", (sid, p["id"], rounds, json.dumps(order)))
        out = serve_round(c, sid, p["id"], order, 0)
    return jsonify(session_id=sid, rounds=rounds, nickname=nick, correct=0, predictions_made=0, **out), 201

def session_row(c, sid, token):
    p = get_player(c, token)
    if not p or not isinstance(sid, str): return None, None
    s = c.execute("SELECT * FROM game_sessions WHERE id=? AND player_id=?", (sid, p["id"])).fetchone()
    return p, s

@app.post("/api/game/answer")
def answer():
    d = body()
    with db.conn() as c:
        p, s = session_row(c, d.get("session_id"), d.get("token"))
        if not s: return err("session not found", 404)
        if s["completed_at"] or not s["pending_json"]: return err("round already answered or game finished", 409)
        pend = json.loads(s["pending_json"]); sc = BY_ID.get(d.get("scenario_id"))
        if not sc or sc["id"] != pend["scenario_id"]: return err("scenario does not match the active round", 400)
        chosen = option(sc, d.get("option_id"))
        if not chosen: return err("invalid option", 400)
        pred = pend["prediction"]; hist_used = len(history(c, p["id"]))
        correct = None if not pred else int(pred["option_id"] == chosen["id"])
        c.execute("UPDATE game_sessions SET pending_json=NULL WHERE id=?", (s["id"],))  # lock the round
        c.execute("INSERT INTO scenario_answers(session_id,scenario_id,selected_option_id,predicted_option_id,prediction_source,prediction_was_correct) VALUES(?,?,?,?,?,?)",
                  (s["id"], sc["id"], chosen["id"], pred["option_id"] if pred else None, pred["source"] if pred else "learning", correct))
        answered = s["rounds_answered"] + 1; made = s["predictions_made"] + (1 if pred else 0); good = s["correct_predictions"] + (correct or 0)
        c.execute("UPDATE game_sessions SET rounds_answered=?,predictions_made=?,correct_predictions=? WHERE id=?", (answered, made, good, s["id"]))
        kind = "learning" if not pred else ("correct" if correct else "wrong")
        why = pred["why"] if pred else "Professor Noodle is still collecting data. Don't judge the little guy yet."
        out = {"chosen": chosen["id"], "predicted": pred["option_id"] if pred else None, "correct": correct, "reaction": eng.reaction(kind, d.get("last_reaction")),
               "kind": kind, "explanation": why, "score": {"correct": good, "predictions_made": made, "accuracy": eng.accuracy(good, made)},
               "round": answered, "rounds": s["rounds_planned"], "finished": answered >= s["rounds_planned"]}
        order = json.loads(s["order_json"])
        if out["finished"]:
            c.execute("UPDATE game_sessions SET completed_at=CURRENT_TIMESTAMP WHERE id=?", (s["id"],))
            out["summary"] = summarise(c, s["id"], hist_used - answered + 1)
        else:
            out["next"] = serve_round(c, s["id"], p["id"], order, answered)
    return jsonify(out)

def summarise(c, sid, used_before):
    s = c.execute("SELECT * FROM game_sessions WHERE id=?", (sid,)).fetchone()
    cats = {}
    for r in c.execute("SELECT scenario_id, prediction_was_correct w FROM scenario_answers WHERE session_id=?", (sid,)):
        if r["w"] is None: continue
        k = BY_ID[r["scenario_id"]]["category"]; v = cats.setdefault(k, [0, 0]); v[0] += r["w"]; v[1] += 1
    acc = eng.accuracy(s["correct_predictions"], s["predictions_made"]); title, text = eng.interpret(acc, s["predictions_made"])
    return {"rounds": s["rounds_answered"], "predictions_made": s["predictions_made"], "correct": s["correct_predictions"],
            "incorrect": s["predictions_made"] - s["correct_predictions"], "accuracy": acc, "title": title, "text": text,
            "history_used": max(used_before, 0),
            "categories": [{"category": k, "correct": v[0], "total": v[1]} for k, v in cats.items() if v[1] >= 2]}

@app.get("/api/game/<sid>")
def game_state(sid):
    with db.conn() as c:
        p, s = session_row(c, sid, request.args.get("token"))
        if not s: return err("session not found", 404)
    return jsonify({k: s[k] for k in ("id", "rounds_planned", "rounds_answered", "predictions_made", "correct_predictions", "started_at", "completed_at")})

@app.get("/api/history")
def hist_api():
    with db.conn() as c:
        p = get_player(c, request.args.get("token"))
        if not p: return jsonify(sessions=[])
        rows = c.execute("SELECT rounds_answered r, predictions_made m, correct_predictions k, started_at t FROM game_sessions WHERE player_id=? AND completed_at IS NOT NULL ORDER BY started_at DESC LIMIT 8", (p["id"],)).fetchall()
    return jsonify(sessions=[{"rounds": r["r"], "made": r["m"], "correct": r["k"], "accuracy": eng.accuracy(r["k"], r["m"]), "date": r["t"]} for r in rows])

@app.get("/api/stats")
def stats():
    with db.conn() as c:
        p = get_player(c, request.args.get("token"))
        empty = {"games": 0, "rounds": 0, "made": 0, "correct": 0, "accuracy": None, "tags": [], "keys": [], "sessions": []}
        if not p: return jsonify(empty)
        t = c.execute("SELECT COUNT(*) g, COALESCE(SUM(rounds_answered),0) r, COALESCE(SUM(predictions_made),0) m, COALESCE(SUM(correct_predictions),0) k FROM game_sessions WHERE player_id=? AND completed_at IS NOT NULL", (p["id"],)).fetchone()
        _, tags, _ = eng.learn(history(c, p["id"]))
        keys = {}
        for h in history(c, p["id"]):
            o = option(BY_ID[h["scenario_id"]], h["option_id"]); keys[o["key"]] = keys.get(o["key"], 0) + 1
    top = lambda d: [{"name": k, "count": v} for k, v in sorted(d.items(), key=lambda x: -x[1])[:6]]
    out = {"games": t["g"], "rounds": t["r"], "made": t["m"], "correct": t["k"], "accuracy": eng.accuracy(t["k"], t["m"]), "tags": top(tags), "keys": top(keys), "nickname": p["nickname"]}
    return jsonify(out)

@app.post("/api/settings/reset")
def reset():
    d = body()
    if d.get("confirm") is not True: return err("confirmation required")
    with db.conn() as c:
        p = get_player(c, d.get("token"))
        if not p: return err("invalid player token")
        c.execute("DELETE FROM game_sessions WHERE player_id=?", (p["id"],))  # cascades to answers; other players untouched
    return jsonify(ok=True)

@app.errorhandler(404)
def nf(e): return err("not found", 404)
@app.errorhandler(500)
def ise(e): return err("something broke on the server", 500)

db.init_db()
if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=False)
