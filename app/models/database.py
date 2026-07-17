# app/models/database.py
import sqlite3
import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL UNIQUE,
                email       TEXT NOT NULL UNIQUE,
                password    TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                name        TEXT NOT NULL,
                description TEXT,
                sector      TEXT,
                location    TEXT,
                status      TEXT DEFAULT 'Active',
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS risks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id      INTEGER NOT NULL REFERENCES projects(id),
                title           TEXT NOT NULL,
                description     TEXT NOT NULL,
                risk_category   TEXT NOT NULL,
                probability     REAL NOT NULL,
                impact          REAL NOT NULL,
                status          TEXT DEFAULT 'Open',
                previous_status TEXT DEFAULT 'Open',
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS risk_classifications (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_id         INTEGER NOT NULL REFERENCES risks(id),
                predicted_label TEXT NOT NULL,
                confidence      REAL NOT NULL,
                all_probs       TEXT,
                accepted        INTEGER DEFAULT 1,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mitigations (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_id               INTEGER NOT NULL REFERENCES risks(id),
                mitigation_id         TEXT NOT NULL,
                description           TEXT NOT NULL,
                implementation_steps  TEXT,
                source                TEXT,
                similarity_score      REAL,
                rank_position         INTEGER,
                created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS feedback_log (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_id             INTEGER NOT NULL REFERENCES risks(id),
                predicted_label     TEXT NOT NULL,
                corrected_label     TEXT NOT NULL,
                confidence          REAL,
                correction_reason   TEXT,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        db.commit()
