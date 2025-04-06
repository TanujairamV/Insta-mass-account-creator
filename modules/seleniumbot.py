""" author: feezyhendrix

    main function botcore
 """

from time import sleep
from random import randint
import logging

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

logging.basicConfig(level=logging.INFO)

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
        matches = re.findall(r"<td>\d+\.\d+\.\d+\.\d+</td><td>\d+</td>", r.text)
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
            account_info = accnt.new_account()

            logging.info(f"Username: {account_info['username']}")

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
            try:
                action_chains.move_to_element(submit_button).click().perform()
            except:
                submit_button.click()
            sleep(5)

            # Fill birthday (Custom dropdown)
            birthday = account_info["birthday"].split(" ")
            try:
                print('Filling birthday details')
                sleep(3)  # let transition complete

                # Month
                month_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Month"]')))
                month_element.click()
                month_option = wait.until(EC.presence_of_element_located((By.XPATH, f'//div[text()="{birthday[0]}"]')))
                month_option.click()
                sleep(0.5)

                # Day
                day_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Day"]')))
                day_element.click()
                day_option = wait.until(EC.presence_of_element_located((By.XPATH, f'//div[text()="{birthday[1].replace(",", "")}"]')))
                day_option.click()
                sleep(0.5)

                # Year
                year_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Year"]')))
                year_element.click()
                year_option = wait.until(EC.presence_of_element_located((By.XPATH, f'//div[text()="{birthday[2]}"]')))
                year_option.click()
                sleep(0.5)

                # Next Button
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Next"]')))
                next_button.click()
                sleep(3)

            except Exception as e:
                driver.save_screenshot("birthday_error.png")
                logging.warning(f"Skipping birthday selection: {e}")

            store(account_info)
            print(f"[INFO] Account created: {account_info['username']}")

        except Exception as e:
            print(f"[FATAL ERROR] {e}")

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
