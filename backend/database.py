import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime

DB_PATH = "liferpg.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 0,
                strength INTEGER DEFAULT 10,
                intelligence INTEGER DEFAULT 10,
                agility INTEGER DEFAULT 10,
                charisma INTEGER DEFAULT 10,
                willpower INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                description TEXT,
                exp_gained INTEGER DEFAULT 0,
                gold_gained INTEGER DEFAULT 0,
                attribute_changes TEXT DEFAULT '{}',
                ai_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );

            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                rarity TEXT DEFAULT '普通',
                stat_bonuses TEXT DEFAULT '{}',
                special_effect TEXT,
                equipped BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );

            CREATE TABLE IF NOT EXISTS titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                unlock_condition TEXT,
                equipped BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                quest_type TEXT DEFAULT 'daily',
                exp_reward INTEGER DEFAULT 0,
                gold_reward INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
        """)


def create_character(name: str) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO characters (name) VALUES (?)",
            (name,)
        )
        conn.commit()
        character_id = cursor.lastrowid
        return get_character(character_id)


def get_character(character_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM characters WHERE id = ?",
            (character_id,)
        ).fetchone()
        if row:
            return dict(row)
    return None


def update_character(character_id: int, **kwargs) -> dict:
    with get_db() as conn:
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [character_id]
        conn.execute(
            f"UPDATE characters SET {set_clause} WHERE id = ?",
            values
        )
        return get_character(character_id)


def add_activity_log(character_id: int, activity_type: str, description: str,
                    exp_gained: int, gold_gained: int,
                    attribute_changes: dict, ai_feedback: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO activity_logs 
               (character_id, activity_type, description, exp_gained, 
                gold_gained, attribute_changes, ai_feedback)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (character_id, activity_type, description, exp_gained,
             gold_gained, json.dumps(attribute_changes), ai_feedback)
        )
        row = conn.execute(
            "SELECT * FROM activity_logs WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_activity_logs(character_id: int, limit: int = 20) -> list:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM activity_logs 
               WHERE character_id = ? 
               ORDER BY created_at DESC LIMIT ?""",
            (character_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def add_equipment(character_id: int, name: str, description: str,
                  rarity: str, stat_bonuses: dict, special_effect: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO equipment 
               (character_id, name, description, rarity, stat_bonuses, special_effect)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (character_id, name, description, rarity,
             json.dumps(stat_bonuses), special_effect)
        )
        row = conn.execute(
            "SELECT * FROM equipment WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_equipment(character_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM equipment WHERE character_id = ? ORDER BY created_at DESC",
            (character_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_title(character_id: int, name: str, description: str,
              unlock_condition: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO titles (character_id, name, description, unlock_condition)
               VALUES (?, ?, ?, ?)""",
            (character_id, name, description, unlock_condition)
        )
        row = conn.execute(
            "SELECT * FROM titles WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_titles(character_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM titles WHERE character_id = ? ORDER BY created_at DESC",
            (character_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_quest(character_id: int, title: str, description: str,
              quest_type: str, exp_reward: int, gold_reward: int,
              due_date: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO quests 
               (character_id, title, description, quest_type, exp_reward, gold_reward, due_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (character_id, title, description, quest_type, exp_reward, gold_reward, due_date)
        )
        row = conn.execute(
            "SELECT * FROM quests WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_quests(character_id: int, status: str = None) -> list:
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM quests WHERE character_id = ? AND status = ? ORDER BY created_at DESC",
                (character_id, status)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quests WHERE character_id = ? ORDER BY created_at DESC",
                (character_id,)
            ).fetchall()
        return [dict(r) for r in rows]


def complete_quest(quest_id: int) -> dict:
    with get_db() as conn:
        conn.execute(
            "UPDATE quests SET status = 'completed' WHERE id = ?",
            (quest_id,)
        )
        row = conn.execute(
            "SELECT * FROM quests WHERE id = ?",
            (quest_id,)
        ).fetchone()
        return dict(row) if row else None
