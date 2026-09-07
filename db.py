import os, sqlite3
from pathlib import Path

DB_PATH = os.environ.get("DATABASE_PATH", str(Path(__file__).parent / "data" / "app.db"))

def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS assessments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token TEXT UNIQUE NOT NULL,
            code TEXT NOT NULL,
            title TEXT NOT NULL,
            areas TEXT NOT NULL,
            inputs TEXT NOT NULL,
            results TEXT NOT NULL,
            reviews TEXT NOT NULL DEFAULT '{}',
            proofreading TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_assessments_token ON assessments(access_token);
        CREATE TABLE IF NOT EXISTS version_assessments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token TEXT UNIQUE NOT NULL,
            code TEXT NOT NULL,
            title TEXT NOT NULL,
            areas TEXT NOT NULL,
            previous_text TEXT NOT NULL,
            current_text TEXT NOT NULL,
            previous_score TEXT NOT NULL,
            current_score TEXT NOT NULL,
            current_proofreading TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_version_assessments_token ON version_assessments(access_token);
        """)
