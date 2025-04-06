""" author: feezyhendrix
    main function botcore
"""

from time import sleep
from random import randint
import re
import logging
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store

class AccountCreator():
    account_created = 0

    def __init__(self, use_custom_proxy, use_local_ip_address):
        self.sockets = []
        self.use_custom_proxy = use_custom_proxy
        self.use_local_ip_address = use_local_ip_address
        self.url = 'https://www.instagram.com/accounts/emailsignup/'
        self.__collect_sockets()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def __collect_sockets(self):
        try:
            r = requests.get("https://www.sslproxies.org/")
            matches = re.findall(r"<td>\d+\.\d+\.\d+\.\d+</td><td>\d+</td>", r.text)
            revised_list = [m1.replace("<td>", "") for m1 in matches]
            for socket_str in revised_list:
                self.sockets.append(socket_str[:-5].replace("</td>", ":"))
        except Exception as e:
            logging.error(f"Could not fetch proxies: {e}")

    def createaccount(self, proxy=None):
        chrome_options = webdriver.ChromeOptions()

        if proxy:
            chrome_options.add_argument('--proxy-server=%s' % proxy)

        chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36"')
        chrome_options.add_argument('window-size=1200x600')

        driver = webdriver.Chrome(
            options=chrome_options,
            executable_path=config.Config['chromedriver_path']
        )

        logging.info("Opening Browser")
        driver.get(self.url)
        sleep(5)

        action_chains = ActionChains(driver)
        sleep(5)

        account_info = accnt.new_account()

        logging.info(f"Gender: {account_info['gender']}")
        logging.info(f"Url generated: {account_info['url']}")
        logging.info(f"Birthday: {account_info['birthday']}")
        logging.info(f"Username: {account_info['username']}")
        logging.info(f"Email: {account_info['email']}")

        try:
            # Fill email
            email_field = driver.find_element(By.NAME, 'emailOrPhone')
            action_chains.move_to_element(email_field)
            email_field.send_keys(str(account_info["email"]))
            sleep(2)

            # Full name
            fullname_field = driver.find_element(By.NAME, 'fullName')
            action_chains.move_to_element(fullname_field)
            fullname_field.send_keys(account_info["name"])
            sleep(2)

            # Username
            username_field = driver.find_element(By.NAME, 'username')
            action_chains.move_to_element(username_field)
            username_field.send_keys(account_info["username"])
            sleep(2)

            # Password
            password_field = driver.find_element(By.NAME, 'password')
            action_chains.move_to_element(password_field)
            password_field.send_keys(account_info["password"])
            sleep(2)

            # Submit form
            submit = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/form/div[7]/div/button')
            action_chains.move_to_element(submit)
            sleep(2)
            submit.click()
            sleep(3)

            # Birthday filling
            try:
                birth_parts = account_info["birthday"].split(" ")  # Ex: ['August', '3,', '1972']
                birth_month = birth_parts[0]
                birth_day = birth_parts[1].replace(',', '')
                birth_year = birth_parts[2]

                month_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select')
                day_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select')
                year_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select')

                month_button.send_keys(birth_month)
                sleep(1)
                day_button.send_keys(birth_day)
                sleep(1)
                year_button.send_keys(birth_year)
                sleep(1)

                next_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
                next_button.click()

            except Exception as e:
                logging.error(f"Birthday Selection Failed: {e}")

            sleep(4)

            # Save account info
            store(account_info)

        except Exception as e:
            logging.error(f"Error during account creation: {e}")
        finally:
            driver.close()

    def creation_config(self):
        try:
            if not self.use_local_ip_address:
                if not self.use_custom_proxy:
                    for i in range(config.Config['amount_of_account']):
                        if self.sockets:
                            current_socket = self.sockets.pop(0)
                            try:
                                self.createaccount(current_socket)
                            except Exception as e:
                                logging.error(f"Error!, Trying another Proxy {current_socket}: {e}")
                                continue
                else:
                    with open(config.Config['proxy_file_path'], 'r') as file:
                        content = file.read().splitlines()
                        for proxy in content:
                            amount = config.Config.get('amount_per_proxy', randint(1, 20))
                            logging.info(f"Creating {amount} users for proxy {proxy}")
                            for _ in range(amount):
                                try:
                                    self.createaccount(proxy)
                                except Exception as e:
                                    logging.error(f"Proxy Error: {e}")
            else:
                for i in range(config.Config['amount_of_account']):
                    try:
                        self.createaccount()
                    except Exception as e:
                        logging.error(f"Error with local IP: {e}")
                        continue
        except Exception as e:
            logging.error(f"Fatal Error in creation_config: {e}")

def runbot():
    account = AccountCreator(
        config.Config['use_custom_proxy'],
        config.Config['use_local_ip_address']
    )
    account.creation_config()
