import sqlite3
import bcrypt

DATABASE = "cyberlab.db"

def get_connection():
    # Keep write contention manageable during Flask debug/reload traffic.
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_plain TEXT,
            password_hashed TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            failed_attempts INTEGER DEFAULT 0,
            locked_until REAL DEFAULT 0
        )
    """)

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            session_id TEXT NOT NULL,
            created_at REAL NOT NULL,
            is_secure INTEGER DEFAULT 0
        )
    """)

    # Attack logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attack_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attack_type TEXT,
            payload TEXT,
            success INTEGER,
            timestamp REAL
        )
    """)

    # Demo users insert
    users = [
        ("admin", "admin123", "admin"),
        ("john", "john@2024", "user"),
        ("alice", "alice@pass", "user"),
    ]

    for username, plain_password, role in users:
        hashed = bcrypt.hashpw(
            plain_password.encode(), 
            bcrypt.gensalt()
        ).decode()
        
        try:
            cursor.execute("""
                INSERT INTO users (username, password_plain, password_hashed, role)
                VALUES (?, ?, ?, ?)
            """, (username, plain_password, hashed, role))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    print("✅ Database ready!")

if __name__ == "__main__":
    setup_database()