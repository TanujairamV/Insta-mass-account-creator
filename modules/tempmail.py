# modules/tempmail.py

import requests
import time
import logging
import random
import string

class TempMailClient:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.session = requests.Session()
        self.account = self._create_account()
        self.token = self._get_token()

    def _generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _create_account(self):
        domains = self.session.get(f"{self.base_url}/domains").json()["hydra:member"]
        domain = random.choice(domains)["domain"]
        email = f"{self._generate_random_string()}@{domain}"
        password = self._generate_random_string(12)

        response = self.session.post(f"{self.base_url}/accounts", json={
            "address": email,
            "password": password
        })

        if response.status_code != 201:
            raise Exception(f"Failed to create account: {response.text}")

        logging.info(f"Email: {email}")
        return {"email": email, "password": password}

    def _get_token(self):
        response = self.session.post(f"{self.base_url}/token", json={
            "address": self.account["email"],
            "password": self.account["password"]
        })

        if response.status_code != 200:
            raise Exception("Could not retrieve token from mail.tm")

        return response.json()["token"]

    def get_email(self):
        return self.account["email"]

    def wait_for_confirmation_code(self, timeout=120):
        logging.info("[INFO] Waiting for confirmation code...")
        start_time = time.time()

        headers = {"Authorization": f"Bearer {self.token}"}

        while time.time() - start_time < timeout:
            messages = self.session.get(f"{self.base_url}/messages", headers=headers).json().get("hydra:member", [])
            for message in messages:
                msg_data = self.session.get(f"{self.base_url}/messages/{message['id']}", headers=headers).json()
                logging.info(f"Received message: {msg_data['subject']}")
                code = self._extract_confirmation_code(msg_data["text"])
                if code:
                    return code
            time.sleep(5)

        raise Exception("Confirmation code not received in time.")

    def _extract_confirmation_code(self, text):
        import re
        match = re.search(r'(?<!\d)(\d{6})(?!\d)', text)
        return match.group(1) if match else None
