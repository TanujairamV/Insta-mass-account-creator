import time
import logging
import requests
import json
import re
from random import randint
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

from modules.config import Config
from modules.generateaccountinformation import new_account
from modules.storeusername import store

# Mail.tm client using API
class TempMailClient:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.domain = self._get_domain()
        self.address = None
        self.password = None
        self.token = None
        self.account_id = None

    def _get_domain(self):
        res = requests.get(f"{self.base_url}/domains")
        domains = res.json()["hydra:member"]
        return domains[0]["domain"]

    def create_account(self):
        name = "user" + str(randint(10000, 99999))
        email = f"{name}@{self.domain}"
        password = "TestPassword123"
        data = {
            "address": email,
            "password": password
        }
        res = requests.post(f"{self.base_url}/accounts", json=data)
        if res.status_code != 201:
            raise Exception(f"Could not create mail.tm account: {res.text}")
        self.address = email
        self.password = password
        logging.info(f"Email: {self.address}")
        return self.address

    def login(self):
        data = {
            "address": self.address,
            "password": self.password
        }
        res = requests.post(f"{self.base_url}/token", json=data)
        if res.status_code != 200:
            raise Exception(f"Login failed: {res.text}")
        self.token = res.json()["token"]
        self.account_id = res.json()["id"]

    def get_confirmation_code(self):
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        for _ in range(60):  # Wait up to 60 seconds
            logging.info("[INFO] Waiting for confirmation code...")
            res = requests.get(f"{self.base_url}/messages", headers=headers)
            msgs = res.json()["hydra:member"]
            if msgs:
                for msg in msgs:
                    if "Instagram" in msg["from"]["address"] or "confirmation" in msg["subject"].lower():
                        message_url = f'{self.base_url}/messages/{msg["id"]}'
                        msg_res = requests.get(message_url, headers=headers)
                        code_match = re.search(r'>(\d{6})<', msg_res.text)
                        if code_match:
                            return code_match.group(1)
            time.sleep(5)
        raise Exception("Confirmation code not received.")

class AccountCreator:
    def __init__(self, use_custom_proxy=False, use_local_ip_address=True):
        self.use_custom_proxy = use_custom_proxy
        self.use_local_ip_address = use_local_ip_address
        self.url = 'https://www.instagram.com/accounts/emailsignup/'

    def createaccount(self):
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--window-size=1200,600")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        service = Service(executable_path=Config['chromedriver_path'])
        driver = webdriver.Chrome(service=service, options=options)

        try:
            logging.info("Opening Browser")
            driver.get(self.url)
            wait = WebDriverWait(driver, 15)
            action = ActionChains(driver)

            mail_client = TempMailClient()
            email = mail_client.create_account()
            mail_client.login()

            acc = new_account()
            acc['email'] = email

            # Fill signup form
            logging.info("Filling email field")
            wait.until(EC.presence_of_element_located((By.NAME, 'emailOrPhone'))).send_keys(acc["email"])
            sleep(1)

            logging.info("Filling fullname field")
            driver.find_element(By.NAME, 'fullName').send_keys(acc["name"])
            sleep(1)

            logging.info("Filling username field")
            driver.find_element(By.NAME, 'username').send_keys(acc["username"])
            sleep(1)

            logging.info("Filling password field")
            driver.find_element(By.NAME, 'password').send_keys(acc["password"])
            sleep(1)

            logging.info("Clicking signup button")
            submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
            action.move_to_element(submit_btn).click().perform()
            sleep(5)

            # Fill birthday
            birthday = acc["birthday"].split(" ")
            try:
                logging.info("Filling birthday details")
                month = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@title="Month:"]')))
                month.send_keys(birthday[0])
                sleep(1)
                day = driver.find_element(By.XPATH, '//select[@title="Day:"]')
                day.send_keys(birthday[1][:-1])
                sleep(1)
                year = driver.find_element(By.XPATH, '//select[@title="Year:"]')
                year.send_keys(birthday[2])
                sleep(1)

                next_btn = driver.find_element(By.XPATH, '//button[text()="Next"]')
                next_btn.click()
                sleep(3)
            except Exception as e:
                logging.warning(f"[WARNING] Skipping birthday selection: {e}")

            # Wait for confirmation code
            confirmation_code = mail_client.get_confirmation_code()
            logging.info(f"Confirmation code received: {confirmation_code}")

            code_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
            code_input.send_keys(confirmation_code)

            confirm_btn = driver.find_element(By.XPATH, '//button[text()="Next"]')
            confirm_btn.click()

            store(acc)
            logging.info(f"[SUCCESS] Account created: {acc['username']} | Password: {acc['password']}")
        except Exception as e:
            logging.error(f"[FATAL ERROR] {e}")

def runbot():
    AccountCreator(Config['use_custom_proxy'], Config['use_local_ip_address']).createaccount()
