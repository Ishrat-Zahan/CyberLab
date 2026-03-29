from flask import Flask, render_template, request, redirect, flash, make_response, jsonify
from auth import secure_login, vulnerable_login, get_all_sessions
from database import get_connection

app = Flask(__name__)
app.secret_key = "dev_secret"


@app.route("/")
def home():
    return render_template("index.html")


# 🔓 Vulnerable login
@app.route("/vuln-login", methods=["GET", "POST"])
def vuln_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user, session_id = vulnerable_login(username, password)

        if user:
            # Weak cookie (no HttpOnly/Secure) for hijacking demo
            resp = make_response(f"✅ Logged in as {user['username']} (role: {user['role']})")
            resp.set_cookie("vuln_session_id", session_id)  # no httponly/secure
            return resp
        else:
            return "❌ Login failed"

    return render_template("login.html")


# 🔐 Secure login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user, session_id, token = secure_login(username, password)

        if user:
            # Secure cookie with HttpOnly/Secure (Secure works over HTTPS)
            resp = redirect("/dashboard")
            resp.set_cookie("secure_session_id", session_id, httponly=True, secure=False, samesite="Lax")
            flash(f"Login successful! Welcome {user['username']}")
            return resp
        else:
            flash(token)
            return redirect("/login")

    return render_template("login.html")


# 💣 Session hijack demo
@app.route("/dashboard")
def dashboard():
    # Demo 1: query-string hijack for weak flows
    session_id = request.args.get("session")

    sessions = get_all_sessions()

    for s in sessions:
        if s["session_id"] == session_id:
            return f"👤 Welcome {s['username']} (session hijacked!)"

    # Demo 2: cookies
    vuln_cookie = request.cookies.get("vuln_session_id")
    if vuln_cookie:
        for s in sessions:
            if s["session_id"] == vuln_cookie:
                return f"👤 Welcome {s['username']} (cookie: vuln_session_id)"

    secure_cookie = request.cookies.get("secure_session_id")
    if secure_cookie:
        for s in sessions:
            if s["session_id"] == secure_cookie:
                return f"✅ Welcome {s['username']} (secure session)"

    return "❌ Invalid session (try supplying ?session=... or login)"


# 🔍 Show sessions
@app.route("/sessions")
def sessions():
    return jsonify(get_all_sessions())


@app.route("/attack-logs")
def attack_logs():
    # Return latest attack logs for quick lab visibility
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, attack_type, payload, success, timestamp FROM attack_logs ORDER BY timestamp DESC LIMIT 50")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

# 🔎 SQL Injection Lab: vulnerable search
@app.route("/vuln-search")
def vuln_search():
    q = request.args.get("q", "")
    conn = get_connection()
    cur = conn.cursor()
    # Intentionally vulnerable (string concatenation)
    sql = f"SELECT id, username, role FROM users WHERE username LIKE '%{q}%'"
    try:
        cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        rows = {"error": str(e)}
    finally:
        conn.close()
    return jsonify({"query": sql, "result": rows})


# 🔒 SQL Injection Lab: secure search
@app.route("/secure-search")
def secure_search():
    q = request.args.get("q", "")
    conn = get_connection()
    cur = conn.cursor()
    sql = "SELECT id, username, role FROM users WHERE username LIKE ?"
    try:
        cur.execute(sql, (f"%{q}%",))
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return jsonify({"query": sql, "params": [f"%{q}%"], "result": rows})


if __name__ == "__main__":
    app.run(debug=True, port=5000)