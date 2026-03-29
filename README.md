## CyberLab (Flask OWASP Practice Lab)

Hands-on security lab to practice OWASP concepts using a small Flask app:

- Vulnerable vs secure SQL queries
- Session hijacking scenarios (weak vs secure cookies)
- Basic attack logging and session visibility
- XSS (vulnerable vs secure)
- CSRF (vulnerable vs secure)

### 1) Prerequisites

- Python 3.10+ (tested on 3.13)
- Git (optional)

On Windows, use PowerShell. On macOS/Linux, use your shell (bash/zsh).

### 2) Clone or Download

```bash
git clone https://github.com/your-org/cyberlab.git
cd cyberlab
```

If you already have the folder, just open it in your terminal.

### 3) Create and Activate a Virtual Environment

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4) Install Dependencies

```bash
pip install -r requirements.txt
```

### 5) Initialize the SQLite Database

This creates tables and demo users.

```bash
python database.py
```

If your Windows console errors on emoji output, you can set UTF-8 first:

```powershell
$env:PYTHONIOENCODING='utf-8'
python database.py
```

### 6) Run the App

```bash
python app.py
```

The app starts at http://127.0.0.1:5000

### 7) Lab Scenarios

- Home: `/` (links to all labs)

SQL Injection:
- Vulnerable: `/vuln-search?q=' OR '1'='1`
- Secure: `/secure-search?q=' OR '1'='1`

Login Flows and Session Hijacking:
- Vulnerable login (sets weak cookie `vuln_session_id`): `/vuln-login`
- Secure login (sets `secure_session_id` with HttpOnly/SameSite): `/login`
- Dashboard (reads query param and cookies):
  - Hijack via query param: `/dashboard?session=<copied_session_id>`
  - Or copy the `vuln_session_id` cookie to another browser/profile and open `/dashboard`

Visibility:
- Recent sessions: `/sessions` (JSON)
- Attack logs: `/attack-logs` (JSON)

XSS:
- Vulnerable reflect: `/xss-vuln`
  - Try: `<script>alert(1)</script>` or `<img src=x onerror=alert(1)>`
- Secure reflect (escaped): `/xss-secure`

CSRF:
- Vulnerable form (no token): `/csrf-vuln`
- Secure form (per-session token): `/csrf-secure`

### 8) Demo Users

- admin / admin123 (role: admin)
- john / john@2024 (role: user)
- alice / alice@pass (role: user)

### 9) Burp Suite (Optional, Recommended)

- Set your browser proxy to `127.0.0.1:8080` (or use Burp’s built-in browser).
- Browse `http://127.0.0.1:5000` through Burp.
- Practice:
  - SQLi: Send `GET /vuln-search?q=' OR '1'='1` to Repeater, iterate payloads; compare with `/secure-search`.
  - Auth brute/enum: Use Intruder on `POST /vuln-login` with username/password lists.
  - Session hijack: Capture `Set-Cookie: vuln_session_id=...`, replay with a different value to `/dashboard`.
  - CSRF: Craft a PoC HTML that auto-POSTs to `/csrf-vuln`; compare with `/csrf-secure` (token required).
  - Logging: Watch `/attack-logs` and `/sessions` to see side effects of your traffic.

### 10) WebGoat (Optional, Complementary)

Run alongside this lab for guided lessons:

```bash
docker run -p 8080:8080 webgoat/webgoat
```

Open `http://127.0.0.1:8080/WebGoat` and use Burp in the middle, just like with CyberLab.

### 11) Troubleshooting

- database is locked:
  - Close any external DB tools (e.g., DB Browser for SQLite) that keep the file open
  - Restart the Flask app
  - We enabled WAL + busy timeout to reduce conflicts, but single-writer limits still apply

- Windows console emoji errors:
  - Set UTF-8: `$env:PYTHONIOENCODING='utf-8'`

### 12) Notes and Safety

- This lab intentionally includes insecure endpoints for learning.
- Use only in a local, isolated environment. Do not expose to the public internet.
- For production, always use parameterized queries, robust session management, HTTPS, CSRF protection, input validation/encoding, and least-privilege DB users.

### 13) Project Structure (high level)

```
app.py            # Flask routes (vulnerable + secure demos)
auth.py           # Login flows, sessions, logging
database.py       # SQLite schema + setup helpers
templates/        # HTML templates
static/           # (optional) static assets
cyberlab.db       # SQLite database (created at runtime)
```

### 14) License

MIT (or your chosen license)

