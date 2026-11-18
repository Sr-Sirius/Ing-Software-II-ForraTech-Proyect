# app/services/chat_service.py
"""
Almacenamiento del chat web (comunicación sincrónica).

Se usa la misma base SQLite del proyecto (app/database.py).
En el plan gratuito de Render el disco es efímero: el historial se borra
cuando el servicio se reinicia o se suspende. El historial completo queda
de todas formas en el grupo de Telegram del equipo.
"""

import time
import uuid

from app.database import get_db


SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(id),
    sender      TEXT NOT NULL CHECK (sender IN ('visitor', 'agent', 'system')),
    author      TEXT NOT NULL,
    text        TEXT NOT NULL,
    channel     TEXT NOT NULL DEFAULT 'web',
    created_at  REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages(session_id, id);

-- Relaciona cada mensaje que el bot publica en el grupo del equipo con
-- la conversación de origen, para enrutar la respuesta.
CREATE TABLE IF NOT EXISTS telegram_links (
    tg_message_id  INTEGER PRIMARY KEY,
    kind           TEXT NOT NULL CHECK (kind IN ('web', 'telegram')),
    target         TEXT NOT NULL,
    created_at     REAL NOT NULL
);
"""

MAX_TEXT = 1000
MAX_NAME = 60


def init_chat_schema(app):
    with app.app_context():
        db = get_db()
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA)
        db.commit()


def clean_text(value, limit):
    value = (value or "").replace("\r", "").strip()
    return value[:limit]


# ─────────────────────────────────────────────
# Sesiones y mensajes
# ─────────────────────────────────────────────
def get_session(session_id):
    if not session_id:
        return None
    row = get_db().execute(
        "SELECT id, name, created_at FROM chat_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    return dict(row) if row else None


def create_session(name):
    session_id = uuid.uuid4().hex
    db = get_db()
    db.execute(
        "INSERT INTO chat_sessions (id, name, created_at) VALUES (?, ?, ?)",
        (session_id, clean_text(name, MAX_NAME) or "Visitante", time.time()),
    )
    db.commit()
    return get_session(session_id)


def short_id(session_id):
    return (session_id or "")[:6].upper()


def add_message(session_id, sender, author, text, channel="web"):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO chat_messages
            (session_id, sender, author, text, channel, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            sender,
            clean_text(author, MAX_NAME) or "ForraTech",
            clean_text(text, MAX_TEXT),
            channel,
            time.time(),
        ),
    )
    db.commit()
    return cursor.lastrowid


def list_messages(session_id, after_id=0):
    rows = get_db().execute(
        """
        SELECT id, sender, author, text, channel, created_at
        FROM chat_messages
        WHERE session_id = ? AND id > ?
        ORDER BY id
        LIMIT 200
        """,
        (session_id, after_id),
    ).fetchall()
    return [dict(r) for r in rows]


def recent_visitor_messages(session_id, seconds):
    row = get_db().execute(
        """
        SELECT COUNT(*) AS n FROM chat_messages
        WHERE session_id = ? AND sender = 'visitor' AND created_at > ?
        """,
        (session_id, time.time() - seconds),
    ).fetchone()
    return row["n"]


# ─────────────────────────────────────────────
# Enlaces Telegram ↔ conversación
# ─────────────────────────────────────────────
def save_link(tg_message_id, kind, target):
    db = get_db()
    db.execute(
        """
        INSERT OR REPLACE INTO telegram_links
            (tg_message_id, kind, target, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (int(tg_message_id), kind, str(target), time.time()),
    )
    db.commit()


def find_link(tg_message_id):
    row = get_db().execute(
        "SELECT tg_message_id, kind, target FROM telegram_links "
        "WHERE tg_message_id = ?",
        (int(tg_message_id),),
    ).fetchone()
    return dict(row) if row else None
