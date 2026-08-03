import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "users.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "is_admin" not in existing_columns:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()


def create_user(username, password):
    conn = get_connection()
    try:
        existing_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        is_admin = 1 if existing_count == 0 else 0
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), is_admin),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, username, password_hash, is_admin FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    user_id, db_username, password_hash, is_admin = row
    if check_password_hash(password_hash, password):
        return {"id": user_id, "username": db_username, "is_admin": bool(is_admin)}
    return None


def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, is_admin, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "username": r[1], "is_admin": bool(r[2]), "created_at": r[3]}
        for r in rows
    ]


def is_user_admin(user_id):
    conn = get_connection()
    row = conn.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False


def count_admins():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1").fetchone()[0]
    conn.close()
    return count


def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
