""" author: feezyhendrix

    main function botcore
 """

import json
from time import sleep
from random import randint

import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re
import logging

MAIL_TM_BASE = "https://api.mail.tm"

def get_mail_tm_account():
    domain = requests.get(f"{MAIL_TM_BASE}/domains").json()["hydra:member"][0]["domain"]
    username = f"user{randint(10000,99999)}@{domain}"
    password = "Password123!"
    
    # Register account
    requests.post(f"{MAIL_TM_BASE}/accounts", json={"address": username, "password": password})
    
    # Get token
    r = requests.post(f"{MAIL_TM_BASE}/token", json={"address": username, "password": password})
    token = r.json()["token"]

    logging.info(f"Email: {username}")
    return username, password, token

def get_confirmation_code(token):
    headers = {"Authorization": f"Bearer {token}"}
    logging.info("[INFO] Waiting for confirmation code...")
    
    for _ in range(30):
        resp = requests.get(f"{MAIL_TM_BASE}/messages", headers=headers).json()
        if resp["hydra:member"]:
            message_id = resp["hydra:member"][0]["id"]
            msg = requests.get(f"{MAIL_TM_BASE}/messages/{message_id}", headers=headers).json()
            match = re.search(r'(\d{6})', msg["text"])
            if match:
                code = match.group(1)
                logging.info(f"[INFO] Confirmation code received: {code}")
                return code
        sleep(2)
    logging.error("[ERROR] No confirmation code received.")
    return None

class AccountCreator():
    account_created = 0

    def __init__(self, use_custom_proxy, use_local_ip_address):
        self.sockets = []
        self.use_custom_proxy = use_custom_proxy
        self.use_local_ip_address = use_local_ip_address
        self.url = 'https://www.instagram.com/accounts/emailsignup/'
        self.__collect_sockets()

    def __collect_sockets(self):
        r = requests.get("https://www.sslproxies.org/")
        matches = re.findall(r"<td>\d+.\d+.\d+.\d+</td><td>\d+</td>", r.text)
        revised_list = [m1.replace("<td>", "") for m1 in matches]
        for socket_str in revised_list:
            self.sockets.append(socket_str[:-5].replace("</td>", ":"))

    def createaccount(self, proxy=None):
        options = Options()
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36')
        options.add_argument('window-size=1200x600')

        service = Service(executable_path=config.Config['chromedriver_path'])
        driver = webdriver.Chrome(service=service, options=options)

        try:
            print('Opening Browser')
            driver.get(self.url)
            print('Browser Opened')

            wait = WebDriverWait(driver, 15)
            action_chains = ActionChains(driver)

            mail_email, mail_password, mail_token = get_mail_tm_account()
            account_info = accnt.new_account()
            account_info["email"] = mail_email

            # Fill email
            print('Filling email field')
            email_field = wait.until(EC.presence_of_element_located((By.NAME, 'emailOrPhone')))
            email_field.send_keys(str(account_info["email"]))
            sleep(1)

            # Fill full name
            print('Filling fullname field')
            fullname_field = driver.find_element(By.NAME, 'fullName')
            fullname_field.send_keys(account_info["name"])
            sleep(1)

            # Fill username
            print('Filling username field')
            username_field = driver.find_element(By.NAME, 'username')
            username_field.send_keys(account_info["username"])
            sleep(1)

            # Fill password
            print('Filling password field')
            password_field = driver.find_element(By.NAME, 'password')
            password_field.send_keys(str(account_info["password"]))
            sleep(1)

            # Submit signup
            print('Clicking signup button')
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
            action_chains.move_to_element(submit_button).click().perform()
            sleep(5)

            # Fill birthday
            birthday = account_info["birthday"].split(" ")
            try:
                print('Filling birthday details')
                month_select = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@title="Month:"]')))
                month_select.send_keys(birthday[0])
                sleep(1)

                day_select = driver.find_element(By.XPATH, '//select[@title="Day:"]')
                day_select.send_keys(birthday[1][:-1])
                sleep(1)

                year_select = driver.find_element(By.XPATH, '//select[@title="Year:"]')
                year_select.send_keys(birthday[2])
                sleep(1)

                next_button = driver.find_element(By.XPATH, '//button[text()="Next"]')
                next_button.click()
                sleep(3)
            except Exception as e:
                print(f"[WARNING] Skipping birthday selection: {e}")

            # Wait for and enter confirmation code
            code = get_confirmation_code(mail_token)
            if code:
                code_input = wait.until(EC.presence_of_element_located((By.NAME, 'email_confirmation_code')))
                code_input.send_keys(code)
                sleep(2)
                confirm_btn = driver.find_element(By.XPATH, '//button[text()="Next"]')
                confirm_btn.click()
                sleep(3)

            store(account_info)
            print(f"[INFO] Account created: {account_info['username']}")
            print(f"[INFO] Username: {account_info['username']}")
            print(f"[INFO] Password: {account_info['password']}")

        except Exception as e:
            print(f"[FATAL ERROR] {e}")

    def creation_config(self):
        try:
            if not self.use_local_ip_address:
                if not self.use_custom_proxy:
                    for _ in range(config.Config['amount_of_account']):
                        if self.sockets:
                            current_socket = self.sockets.pop(0)
                            try:
                                self.createaccount(current_socket)
                            except Exception as e:
                                print(f'Error! Trying another Proxy: {current_socket} => {e}')
                                self.createaccount(current_socket)
                else:
                    with open(config.Config['proxy_file_path'], 'r') as file:
                        content = file.read().splitlines()
                        for proxy in content:
                            amount_per_proxy = config.Config['amount_per_proxy']
                            count = amount_per_proxy if amount_per_proxy != 0 else randint(1, 20)
                            print(f"Creating {count} accounts for this proxy")
                            for _ in range(count):
                                try:
                                    self.createaccount(proxy)
                                except Exception as e:
                                    print(f"An error has occurred: {e}")
            else:
                for _ in range(config.Config['amount_of_account']):
                    try:
                        self.createaccount()
                    except Exception as e:
                        print(f'Error! Check — your IP might be banned. Reason: {e}')
                        self.createaccount()

        except Exception as e:
            print(f"[FATAL ERROR] {e}")

def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()
