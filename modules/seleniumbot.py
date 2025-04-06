import time
import random
import string
import re
import hashlib
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

import modules.generateaccountinformation as accnt
from modules.storeusername import store
from modules.config import Config

TEMP_MAIL_API_URL = "https://api.temp-mail.org/request"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_temp_email():
    domains = requests.get(f"{TEMP_MAIL_API_URL}/domains/").json()
    email_name = generate_random_string()
    email = f"{email_name}@{domains[0]}"
    return email, email_name

def get_inbox_hash(email):
    return hashlib.md5(email.encode()).hexdigest()

def get_confirmation_code(email):
    email_hash = get_inbox_hash(email)
    print(f"[INFO] Waiting for confirmation code for {email}")
    for _ in range(60):  # Wait up to 60s
        try:
            inbox = requests.get(f"{TEMP_MAIL_API_URL}/mail/id/{email_hash}/", headers=HEADERS).json()
            if isinstance(inbox, list) and len(inbox) > 0:
                message = inbox[0]
                mail_text = message.get("mail_text", "")
                match = re.search(r"\b\d{6}\b", mail_text)
                if match:
                    return match.group(0)
        except Exception as e:
            print(f"[DEBUG] No email yet: {e}")
        time.sleep(5)
    raise Exception("Confirmation code not received.")

class AccountCreator:
    def __init__(self):
        self.url = 'https://www.instagram.com/accounts/emailsignup/'

    def create_account(self):
        email, login = create_temp_email()
        account_info = accnt.new_account()
        account_info["email"] = email

        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(Config["chromedriver_path"])
        driver = webdriver.Chrome(service=service, options=options)

        wait = WebDriverWait(driver, 20)
        driver.get(self.url)
        action = ActionChains(driver)

        try:
            print("[INFO] Filling signup form...")
            wait.until(EC.presence_of_element_located((By.NAME, 'emailOrPhone'))).send_keys(email)
            driver.find_element(By.NAME, 'fullName').send_keys(account_info['name'])
            driver.find_element(By.NAME, 'username').send_keys(account_info['username'])
            driver.find_element(By.NAME, 'password').send_keys(account_info['password'])

            time.sleep(2)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(4)

            print("[INFO] Selecting birthday...")
            birthday = account_info["birthday"].split(" ")
            wait.until(EC.presence_of_element_located((By.XPATH, '//select[@title="Month:"]'))).send_keys(birthday[0])
            driver.find_element(By.XPATH, '//select[@title="Day:"]').send_keys(birthday[1][:-1])
            driver.find_element(By.XPATH, '//select[@title="Year:"]').send_keys(birthday[2])
            driver.find_element(By.XPATH, '//button[text()="Next"]').click()
            time.sleep(5)

            print("[INFO] Getting confirmation code...")
            code = get_confirmation_code(email)
            if code:
                print(f"[INFO] Confirmation code received: {code}")
                wait.until(EC.presence_of_element_located((By.NAME, 'email_confirmation_code'))).send_keys(code)
                driver.find_element(By.XPATH, '//button[text()="Next"]').click()
            else:
                print("[ERROR] Confirmation code not found.")
                return

            store(account_info)

            print("\n✅ Account Created Successfully!")
            print(f"Username: {account_info['username']}")
            print(f"Password: {account_info['password']}")
            print(f"Email: {account_info['email']}\n")

            input("Press ENTER to close the browser...")

        except Exception as e:
            print(f"[FATAL ERROR] {e}")
            input("Press ENTER to close the browser manually...")
        finally:
            driver.quit()

def runbot():
    bot = AccountCreator()
    bot.create_account()
