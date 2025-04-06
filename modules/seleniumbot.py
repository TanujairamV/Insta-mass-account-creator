import logging
import random
import re
import time
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select

import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store


logging.basicConfig(level=logging.INFO)

class AccountCreator:
    def __init__(self, use_custom_proxy, use_local_ip_address):
        self.use_custom_proxy = use_custom_proxy
        self.use_local_ip_address = use_local_ip_address
        self.url = 'https://www.instagram.com/accounts/emailsignup/'
        self.sockets = self.__collect_sockets()

    def __collect_sockets(self):
        r = requests.get("https://www.sslproxies.org/")
        matches = re.findall(r"<td>\d+\.\d+\.\d+\.\d+</td><td>\d+</td>", r.text)
        return [m.replace("<td>", "").replace("</td>", "").replace(":", ":") for m in matches]

    def createaccount(self, proxy=None):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('window-size=1200x600')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'
        )
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')

        driver = webdriver.Chrome(
            service=Service(config.Config['chromedriver_path']),
            options=chrome_options
        )

        logging.info("Opening Browser")
        driver.get(self.url)
        time.sleep(5)

        account_info = accnt.new_account()
        logging.info(f"Email: {account_info['email']}")
        logging.info(f"Gender: {account_info['gender']}")
        logging.info(f"Url generated: {account_info['url']}")
        logging.info(f"Birthday: {account_info['birthday']}")
        logging.info(f"Username: {account_info['username']}")

        driver.find_element(By.NAME, "emailOrPhone").send_keys(account_info["email"])
        logging.info("Filling email field")

        driver.find_element(By.NAME, "fullName").send_keys(account_info["name"])
        logging.info("Filling fullname field")

        driver.find_element(By.NAME, "username").send_keys(account_info["username"])
        logging.info("Filling username field")

        driver.find_element(By.NAME, "password").send_keys(account_info["password"])
        logging.info("Filling password field")

        time.sleep(2)

        try:
            signup_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
            signup_button.click()
            logging.info("Clicking signup button")
        except Exception as e:
            logging.warning(f"[ERROR] Could not click signup button: {e}")

        time.sleep(5)

        try:
            month = Select(driver.find_element(By.XPATH, '//select[@title="Month:"]'))
            day = Select(driver.find_element(By.XPATH, '//select[@title="Day:"]'))
            year = Select(driver.find_element(By.XPATH, '//select[@title="Year:"]'))

            birthday_parts = account_info["birthday"].split(" ")
            month.select_by_visible_text(birthday_parts[0])
            day.select_by_visible_text(birthday_parts[1][:-1])
            year.select_by_visible_text(birthday_parts[2])

            logging.info("Filling birthday details")

            next_button = driver.find_element(By.XPATH, '//button[text()="Next"]')
            next_button.click()

        except Exception as e:
            logging.warning(f"[WARNING] Skipping birthday selection: {e}")

        # Ask user to manually enter the confirmation code
        logging.info("[INFO] Waiting for confirmation code...")
        user_email = input("Enter your email used for signup: ").strip()
        confirmation_code = input("Enter the confirmation code received: ").strip()

        # You can automate entry here if you know the input field name
        # For now, we just wait to keep the session alive
        time.sleep(10)

        store(account_info)
        driver.quit()

    def creation_config(self):
        try:
            if self.use_local_ip_address:
                for _ in range(config.Config['amount_of_account']):
                    try:
                        self.createaccount()
                    except Exception as e:
                        logging.error(f"Error with local IP: {e}")
            elif self.use_custom_proxy:
                with open(config.Config['proxy_file_path'], 'r') as file:
                    for proxy in file.read().splitlines():
                        for _ in range(config.Config['amount_per_proxy']):
                            try:
                                self.createaccount(proxy)
                            except Exception as e:
                                logging.warning(f"Error with custom proxy {proxy}: {e}")
            else:
                for _ in range(config.Config['amount_of_account']):
                    if self.sockets:
                        proxy = self.sockets.pop(0)
                        try:
                            self.createaccount(proxy)
                        except Exception as e:
                            logging.warning(f"Error with socket proxy {proxy}: {e}")
        except Exception as e:
            logging.error(f"General error: {e}")

def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()
