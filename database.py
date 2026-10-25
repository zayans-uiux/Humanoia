"""SQLite helpers. All SQL is parameterised."""
import sqlite3, os
DB_PATH = os.environ.get("BRAINROT_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "brainrot.db"))
def conn():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def init_db():
    with conn() as c:
        c.executescript("""
CREATE TABLE IF NOT EXISTS players(id INTEGER PRIMARY KEY, token TEXT UNIQUE NOT NULL, nickname TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS game_sessions(id TEXT PRIMARY KEY, player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
 rounds_planned INTEGER, rounds_answered INTEGER DEFAULT 0, predictions_made INTEGER DEFAULT 0, correct_predictions INTEGER DEFAULT 0,
 order_json TEXT, pending_json TEXT, started_at TEXT DEFAULT CURRENT_TIMESTAMP, completed_at TEXT);
CREATE TABLE IF NOT EXISTS scenario_answers(id INTEGER PRIMARY KEY, session_id TEXT NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
 scenario_id TEXT, selected_option_id TEXT, predicted_option_id TEXT, prediction_source TEXT, prediction_was_correct INTEGER, answered_at TEXT DEFAULT CURRENT_TIMESTAMP);""")
