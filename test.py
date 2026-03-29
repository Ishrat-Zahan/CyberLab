from auth import secure_login

print("Testing secure login...")

user, session, token = secure_login("john", "john@2024")

if user:
    print(f"User: {user['username']}")
    print(f"Session: {session}")
    print(f"Token: {token[:30]}...")
else:
    print("Login failed!")