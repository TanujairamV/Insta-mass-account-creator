import logging
import re
import requests
from time import sleep
from random import randint
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store
from modules.tempmail import TempMailClient

class AccountCreator:
    def __init__(self, use_custom_proxy, use_local_ip_address):
        self.use_custom_proxy = use_custom_proxy
        self.use_local_ip_address = use_local_ip_address
        self.sockets = []
        self.url = 'https://www.instagram.com/accounts/emailsignup/'
        self.__collect_sockets()

    def __collect_sockets(self):
        try:
            r = requests.get("https://www.sslproxies.org/")
            matches = re.findall(r"<td>\d+.\d+.\d+.\d+</td><td>\d+</td>", r.text)
            revised_list = [m1.replace("<td>", "") for m1 in matches]
            for socket_str in revised_list:
                self.sockets.append(socket_str[:-5].replace("</td>", ":"))
        except Exception as e:
            logging.warning(f"[WARNING] Could not fetch proxies: {e}")

    def createaccount(self, proxy=None):
        chrome_options = webdriver.ChromeOptions()
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        chrome_options.add_argument('window-size=1200x600')

        driver = webdriver.Chrome(options=chrome_options, executable_path=config.Config['chromedriver_path'])
        logging.info("Opening Browser")
        driver.get(self.url)
        logging.info("Browser Opened")
        sleep(5)

        try:
            action_chains = ActionChains(driver)
            account_info = accnt.new_account()

            # Mail.tm account setup
            mail_client = TempMailClient()
            mail_address = mail_client.address
            logging.info(f"Email: {mail_address}")
            account_info['email'] = mail_address

            # Fill in form
            logging.info("Filling email field")
            email_field = driver.find_element(By.NAME, 'emailOrPhone')
            email_field.send_keys(mail_address)
            sleep(1)

            logging.info("Filling fullname field")
            full_field = driver.find_element(By.NAME, 'fullName')
            full_field.send_keys(account_info["name"])
            sleep(1)

            logging.info("Filling username field")
            user_field = driver.find_element(By.NAME, 'username')
            user_field.send_keys(account_info["username"])
            sleep(1)

            logging.info("Filling password field")
            pass_field = driver.find_element(By.NAME, 'password')
            pass_field.send_keys(account_info["password"])
            sleep(2)

            logging.info("Clicking signup button")
            signup_btn = driver.find_element(By.XPATH, '//form//button[@type="submit"]')
            action_chains.move_to_element(signup_btn).perform()
            signup_btn.click()
            sleep(5)

            # Select Birthday
            logging.info("Filling birthday details")
            try:
                month, day, year = account_info["birthday"].split(" ")
                month_select = driver.find_element(By.XPATH, '//select[@title="Month:"]')
                day_select = driver.find_element(By.XPATH, '//select[@title="Day:"]')
                year_select = driver.find_element(By.XPATH, '//select[@title="Year:"]')

                month_select.send_keys(month)
                day_select.send_keys(day.replace(",", ""))
                year_select.send_keys(year)

                sleep(1)
                next_button = driver.find_element(By.XPATH, '//button[contains(text(), "Next")]')
                next_button.click()
                logging.info("Birthday submitted")
            except Exception as e:
                logging.warning(f"[WARNING] Skipping birthday selection: {e}")

            # Wait for confirmation code
            logging.info("[INFO] Waiting for confirmation code...")
            code = None
            for _ in range(30):
                code = mail_client.get_latest_code()
                if code:
                    break
                sleep(2)

            if code:
                logging.info(f"[INFO] Confirmation code received: {code}")
                input_box = driver.find_element(By.NAME, 'email_confirmation_code')
                input_box.send_keys(code)
                confirm_btn = driver.find_element(By.XPATH, '//button[contains(text(), "Next")]')
                confirm_btn.click()
            else:
                logging.error("[ERROR] No confirmation code received.")

            # Store account
            store(account_info)
            logging.info(f"Account created: {account_info['username']}")

        except Exception as e:
            logging.error(f"[FATAL ERROR] {e}")
        finally:
            driver.quit()

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
                                logging.error(f"Proxy error {current_socket}: {e}")
                else:
                    with open(config.Config['proxy_file_path'], 'r') as file:
                        proxies = file.read().splitlines()
                        for proxy in proxies:
                            for _ in range(config.Config.get('amount_per_proxy', 1)):
                                try:
                                    self.createaccount(proxy)
                                except Exception as e:
                                    logging.error(f"Proxy error {proxy}: {e}")
            else:
                for _ in range(config.Config['amount_of_account']):
                    try:
                        self.createaccount()
                    except Exception as e:
                        logging.error(f"Error with local IP: {e}")
        except Exception as e:
            logging.error(f"[FATAL ERROR] {e}")

def runbot():
    creator = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    creator.creation_config()
