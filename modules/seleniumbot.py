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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

        print('Opening Browser')
        driver.get(self.url)
        print('Browser Opened')
        sleep(5)

        action_chains = ActionChains(driver)
        account_info = accnt.new_account()

        # Fill email
        print('Filling email field')
        email_field = driver.find_element(By.NAME, 'emailOrPhone')
        action_chains.move_to_element(email_field)
        email_field.send_keys(str(account_info["email"]))
        sleep(2)

        # Fill full name
        print('Filling fullname field')
        fullname_field = driver.find_element(By.NAME, 'fullName')
        action_chains.move_to_element(fullname_field)
        fullname_field.send_keys(account_info["name"])
        sleep(2)

        # Fill username
        print('Filling username field')
        username_field = driver.find_element(By.NAME, 'username')
        action_chains.move_to_element(username_field)
        username_field.send_keys(account_info["username"])
        sleep(2)

        # Fill password
        print('Filling password field')
        password_field = driver.find_element(By.NAME, 'password')
        action_chains.move_to_element(password_field)
        password_field.send_keys(str(account_info["password"]))
        sleep(2)

        # Click sign up
        submit = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/form/div[7]/div/button')
        action_chains.move_to_element(submit)
        sleep(2)
        submit.click()
        sleep(3)

        try:
            birthday = account_info["birthday"].split(" ")
            month_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select')
            month_button.send_keys(birthday[0])
            sleep(1)

            day_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select')
            day_button.send_keys(birthday[1][:-1])
            sleep(1)

            year_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select')
            year_button.send_keys(birthday[2])
            sleep(2)

            next_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
            next_button.click()

        except Exception as e:
            print(f"[WARNING] Skipping birthday selection: {e}")

        sleep(4)
        store(account_info)

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
                                print(f'Error! Trying another Proxy: {current_socket}')
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
                        print('Error! Check — your IP might be banned.')
                        self.createaccount()

        except Exception as e:
            print(f"[FATAL ERROR] {e}")

def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()
