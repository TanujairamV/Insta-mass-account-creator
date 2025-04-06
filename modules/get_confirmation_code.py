import time
import requests
import re

def get_code_from_email(username, domain="1secmail.com", retries=10, delay=5):
    email = f"{username}@{domain}"
    login, domain = email.split("@")

    print(f"[INFO] Waiting for confirmation code at {email}...")

    for attempt in range(retries):
        time.sleep(delay)
        resp = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}")
        messages = resp.json()

        if messages:
            mail_id = messages[0]['id']
            content = requests.get(
                f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={mail_id}"
            ).json()

            body = content.get("body", "")
            code_match = re.search(r"(\d{6})", body)
            if code_match:
                print(f"[INFO] Code received: {code_match.group(1)}")
                return code_match.group(1)

    print("[ERROR] Confirmation email not received.")
    return None
