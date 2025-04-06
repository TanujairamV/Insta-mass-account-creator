""" author: feezyhendrix

    main function botcore
"""

from time import sleep
from random import randint
import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import requests
import re
import logging


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
        chrome_options = webdriver.ChromeOptions()

        if proxy:
            chrome_options.add_argument('--proxy-server=%s' % proxy)

        chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36"')
        chrome_options.add_argument('window-size=1200x600')

        service = Service(config.Config['chromedriver_path'])
        driver = webdriver.Chrome(service=service, options=chrome_options)

        logging.info("Opening Browser")
        driver.get(self.url)

        sleep(5)
        action_chains = ActionChains(driver)
        sleep(5)

        account_info = accnt.new_account()

        # Fill email
        logging.info("Filling email")
        email_field = driver.find_element(By.NAME, 'emailOrPhone')
        action_chains.move_to_element(email_field)
        email_field.send_keys(account_info["email"])
        sleep(2)

        # Fill full name
        logging.info("Filling full name")
        fullname_field = driver.find_element(By.NAME, 'fullName')
        action_chains.move_to_element(fullname_field)
        fullname_field.send_keys(account_info["name"])
        sleep(2)

        # Fill username
        logging.info("Filling username")
        username_field = driver.find_element(By.NAME, 'username')
        action_chains.move_to_element(username_field)
        username_field.send_keys(account_info["username"])
        sleep(2)

        # Fill password
        logging.info("Filling password")
        password_field = driver.find_element(By.NAME, 'password')
        action_chains.move_to_element(password_field)
        password_field.send_keys(account_info["password"])
        sleep(2)

        # Click Sign up
        submit = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/form/div[7]/div/button')
        action_chains.move_to_element(submit)
        sleep(2)
        submit.click()
        sleep(5)

        # Fill birthday
        try:
            logging.info("Filling birthday")
            birthday_parts = account_info["birthday"].split(" ")
            month, day, year = birthday_parts[0], birthday_parts[1][:-1], birthday_parts[2]

            month_dropdown = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select')
            day_dropdown = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select')
            year_dropdown = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select')

            month_dropdown.send_keys(month)
            day_dropdown.send_keys(day)
            year_dropdown.send_keys(year)

            sleep(2)

            next_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
            next_button.click()

        except Exception as e:
            logging.warning(f"Birthday input failed: {e}")

        sleep(4)

        # Save account
        store(account_info)

        # driver.get(confirm_url) — can be used if activation is added
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
                                logging.warning(f"Error!, Retrying with proxy {current_socket}: {e}")
                                continue
                else:
                    with open(config.Config['proxy_file_path'], 'r') as file:
                        proxies = file.read().splitlines()
                        for proxy in proxies:
                            amount = config.Config.get('amount_per_proxy', 0) or randint(1, 20)
                            logging.info(f"Creating {amount} users with proxy {proxy}")
                            for _ in range(amount):
                                try:
                                    self.createaccount(proxy)
                                except Exception as e:
                                    logging.warning(f"Proxy error: {e}")
            else:
                for _ in range(config.Config['amount_of_account']):
                    try:
                        self.createaccount()
                    except Exception as e:
                        logging.error(f"Error with local IP: {e}")
                        continue
        except Exception as e:
            logging.critical(f"Fatal Error: {e}")


def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()
