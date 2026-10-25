import os, tempfile
os.environ["BRAINROT_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
import app as A, prediction_engine as eng
from scenarios import SCENARIOS, BY_ID
c = A.app.test_client(); T = "tok-test-12345"; T2 = "tok-other-12345"

def test_engine_cold_start_and_accuracy():
    assert eng.predict([], SCENARIOS[0]) is None
    assert eng.accuracy(0, 0) is None and eng.accuracy(2, 3) == 66.7
def test_engine_learns_category_pattern():
    h = [{"scenario_id": "s01", "option_id": "A"}, {"scenario_id": "s02", "option_id": "A"}, {"scenario_id": "s03", "option_id": "A"}]
    p = eng.predict(h, BY_ID["s01"]); assert p["option_id"] == "A" and p["source"] in ("combined", "category")
def test_flow_validation_and_duplicates():
    assert c.get("/").status_code == 200 and len(c.get("/api/scenarios").json) >= 12
    assert c.post("/api/game/start", json={"token": T, "rounds": 7}).status_code == 400
    d = c.post("/api/game/start", json={"token": T, "rounds": 5, "nickname": "<b>x</b>"}).json
    sid, sc = d["session_id"], d["scenario"]["id"]
    assert c.post("/api/game/answer", json={"token": T, "session_id": sid, "scenario_id": sc, "option_id": "Z"}).status_code == 400
    assert c.post("/api/game/answer", json={"token": T2, "session_id": sid, "scenario_id": sc, "option_id": "A"}).status_code == 404
    for i in range(5):
        r = c.post("/api/game/answer", json={"token": T, "session_id": sid, "scenario_id": sc, "option_id": "A"}); assert r.status_code == 200
        assert c.post("/api/game/answer", json={"token": T, "session_id": sid, "scenario_id": sc, "option_id": "A"}).status_code in (409, 400)
        if r.json["finished"]: break
        sc = r.json["next"]["scenario"]["id"]
    assert r.json["finished"] and r.json["summary"]["rounds"] == 5
    s = c.get(f"/api/stats?token={T}").json; assert s["games"] == 1 and s["rounds"] == 5
def test_reset_only_own_data():
    d = c.post("/api/game/start", json={"token": T2, "rounds": 5}).json
    assert c.post("/api/settings/reset", json={"token": T}).status_code == 400
    assert c.post("/api/settings/reset", json={"token": T, "confirm": True}).status_code == 200
    assert c.get(f"/api/stats?token={T}").json["games"] == 0
    assert c.get(f"/api/game/{d['session_id']}?token={T2}").status_code == 200
    assert c.get("/api/stats?token=nobody-nobody").json["accuracy"] is None

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("ok", n)
