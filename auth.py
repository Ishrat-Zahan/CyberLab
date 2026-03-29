import sqlite3
import bcrypt
import secrets
import jwt
import time
from database import get_connection, DATABASE

SECRET_KEY = "cyberlab_secret_key_2024"
LOCKOUT_LIMIT = 3
LOCKOUT_TIME = 60

# ============================================================
# VULNERABLE LOGIN ❌
# ============================================================

def vulnerable_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    # ❌ SQL Injection possible!
    query = f"SELECT * FROM users WHERE username='{username}' AND password_plain='{password}'"
    
    print(f"\n   [DEBUG] Query: {query}")

    try:
        cursor.execute(query)
        user = cursor.fetchone()
    except Exception as e:
        print(f"   [ERROR] {e}")
        # Ensure the read connection is released before any further DB writes.
        conn.close()
        log_attack("SQL_INJECTION_ATTEMPT", f"username={username}", f"error={e}")
        return None, None

    conn.close()
    log_attack("SQL_INJECTION_ATTEMPT", f"username={username}", query)

    if user:
        session_id = f"session_{username}_001"  # ❌ Predictable
        save_session(username, session_id, is_secure=False)
        return dict(user), session_id

    return None, None

# ============================================================
# SECURE LOGIN ✅
# ============================================================

def secure_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    # Check lockout
    cursor.execute("SELECT failed_attempts, locked_until FROM users WHERE username=?", (username,))
    user_data = cursor.fetchone()

    if not user_data:
        conn.close()
        return None, None, "❌ User not found!"

    failed, locked_until = user_data["failed_attempts"], user_data["locked_until"]

    if locked_until and time.time() < locked_until:
        remaining = int(locked_until - time.time())
        conn.close()
        return None, None, f"🔒 Account locked! Try again in {remaining} seconds."

    # ✅ Parameterized query
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode(), user["password_hashed"].encode()):
        # Reset failed attempts
        cursor.execute("UPDATE users SET failed_attempts=0, locked_until=0 WHERE username=?", (username,))
        conn.commit()

        session_id = secrets.token_hex(32)  # ✅ Random
        token = create_jwt(username, user["role"])
        save_session(username, session_id, is_secure=True)

        conn.close()
        return dict(user), session_id, token

    else:
        # Record failed attempt
        new_attempts = failed + 1
        locked_until = time.time() + LOCKOUT_TIME if new_attempts >= LOCKOUT_LIMIT else 0
        cursor.execute("""
            UPDATE users 
            SET failed_attempts=?, locked_until=? 
            WHERE username=?
        """, (new_attempts, locked_until, username))
        conn.commit()
        conn.close()

        if new_attempts >= LOCKOUT_LIMIT:
            return None, None, f"🔒 Too many attempts! Locked for {LOCKOUT_TIME} seconds."
        
        return None, None, f"❌ Wrong password! Attempt {new_attempts}/{LOCKOUT_LIMIT}"

# ============================================================
# JWT
# ============================================================

def create_jwt(username, role):
    payload = {
        "username": username,
        "role": role,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "❌ Token expired!"
    except jwt.InvalidTokenError:
        return None, "❌ Invalid token!"

# ============================================================
# SESSION
# ============================================================

def save_session(username, session_id, is_secure):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (username, session_id, created_at, is_secure)
            VALUES (?, ?, ?, ?)
        """, (username, session_id, time.time(), 1 if is_secure else 0))
        conn.commit()
    except sqlite3.OperationalError as e:
        # Session write is non-critical for this lab flow; avoid crashing request.
        if "database is locked" in str(e).lower():
            print("   [WARN] Session write skipped: database is locked")
        else:
            raise
    finally:
        conn.close()

def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10")
    sessions = cursor.fetchall()
    conn.close()
    return [dict(s) for s in sessions]

# ============================================================
# ATTACK LOGS
# ============================================================

def log_attack(attack_type, payload, result):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attack_logs (attack_type, payload, success, timestamp)
            VALUES (?, ?, ?, ?)
        """, (attack_type, payload, 1, time.time()))
        conn.commit()
    except sqlite3.OperationalError as e:
        # Logging failure should not break the login endpoint.
        if "database is locked" in str(e).lower():
            print("   [WARN] Attack log skipped: database is locked")
        else:
            raise
    finally:
        conn.close()

def get_attack_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attack_logs ORDER BY timestamp DESC LIMIT 20")
    logs = cursor.fetchall()
    conn.close()
    return [dict(l) for l in logs]