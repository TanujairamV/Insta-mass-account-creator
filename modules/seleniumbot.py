"""
author: feezyhendrix (edited by Tanujairam)
Selenium bot to create Instagram account using Tempr.email
"""

import re
import time
import random
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store

TEMP_EMAIL_API = "https://api.tempr.email"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_tempr_email():
    response = requests.get(f"{TEMP_EMAIL_API}/request/domains/", headers=HEADERS)
    domains = response.json()["domains"]
    domain = random.choice(domains)

    name = "user" + str(random.randint(10000, 99999))
    email = f"{name}@{domain}"
    return email, name, domain

def get_confirmation_code(login, domain):
    print(f"[INFO] Waiting for confirmation code at {login}@{domain}...")
    for _ in range(60):  # Wait up to 60 seconds
        try:
            inbox = requests.get(f"{TEMP_EMAIL_API}/request/mail/id/{login}/{domain}/", headers=HEADERS)
            emails = inbox.json()
            if isinstance(emails, list) and len(emails) > 0:
                for email in emails:
                    if 'Instagram' in email.get("subject", ""):
                        mail_id = email["id"]
                        message = requests.get(f"{TEMP_EMAIL_API}/request/source/id/{login}/{domain}/{mail_id}/", headers=HEADERS)
                        match = re.search(r'>(\d{6})<', message.text)
                        if match:
                            code = match.group(1)
                            print(f"[INFO] Confirmation code received: {code}")
                            return code
        except Exception as e:
            print(f"[DEBUG] Waiting for code... {e}")
        time.sleep(5)
    raise Exception("Confirmation code not received in time")

class AccountCreator:
    def __init__(self, use_custom_proxy, use_local_ip_address):
        self.url = 'https://www.instagram.com/accounts/emailsignup/'
        self.use_custom_proxy = use_custom_proxy
        self.use_local_ip_address = use_local_ip_address

    def createaccount(self):
        email, login, domain = get_tempr_email()

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(config.Config['chromedriver_path'])
        driver = webdriver.Chrome(service=service, options=options)

        print("[INFO] Opening Instagram signup page...")
        driver.get(self.url)
        wait = WebDriverWait(driver, 20)
        action = ActionChains(driver)

        account_info = accnt.new_account()
        account_info["email"] = email

        try:
            print("[INFO] Filling form...")
            wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone"))).send_keys(email)
            driver.find_element(By.NAME, "fullName").send_keys(account_info["name"])
            driver.find_element(By.NAME, "username").send_keys(account_info["username"])
            driver.find_element(By.NAME, "password").send_keys(account_info["password"])

            time.sleep(2)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(5)

            print("[INFO] Filling birthday info...")
            birthday = account_info["birthday"].split(" ")
            wait.until(EC.presence_of_element_located((By.XPATH, '//select[@title="Month:"]'))).send_keys(birthday[0])
            driver.find_element(By.XPATH, '//select[@title="Day:"]').send_keys(birthday[1][:-1])
            driver.find_element(By.XPATH, '//select[@title="Year:"]').send_keys(birthday[2])
            driver.find_element(By.XPATH, '//button[text()="Next"]').click()
            time.sleep(5)

            print("[INFO] Waiting for confirmation code...")
            confirmation_code = get_confirmation_code(login, domain)

            code_input = wait.until(EC.presence_of_element_located((By.NAME, 'email_confirmation_code')))
            code_input.send_keys(confirmation_code)
            driver.find_element(By.XPATH, '//button[text()="Next"]').click()

            store(account_info)
            print(f"[SUCCESS] Account created: {account_info['username']} / {account_info['password']}")

        except Exception as e:
            print(f"[FATAL ERROR] {e}")
        finally:
            input("Press Enter to close the browser manually...")
            driver.quit()

def runbot():
    creator = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    creator.createaccount()
