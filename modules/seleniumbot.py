from time import sleep
from random import randint

import modules.config as config
# importing generated info
import modules.generateaccountinformation as accnt
from modules.storeusername import store
# from .activate_account import get_activation_url
# library import
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
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
        # Collect proxy sockets (this part stays the same)
        r = requests.get("https://www.sslproxies.org/")
        matches = re.findall(r"<td>\d+.\d+.\d+.\d+</td><td>\d+</td>", r.text)
        revised_list = [m1.replace("<td>", "") for m1 in matches]
        for socket_str in revised_list:
            self.sockets.append(socket_str[:-5].replace("</td>", ":"))

    def createaccount(self, proxy=None):
        chrome_options = Options()
        if proxy:
            chrome_options.add_argument('--proxy-server=%s' % proxy)

        # Set user-agent and window size
        chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36"')
        chrome_options.add_argument('window-size=1200x600')

        # Path to your ChromeDriver
        driver_path = config.Config['chromedriver_path']

        # Initialize the driver with Service object to resolve `executable_path` issue
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(self.url)
        sleep(5)

        action_chains = ActionChains(driver)
        sleep(5)
        account_info = accnt.new_account()

        # Fill the email field
        print('Filling email field')
        email_field = driver.find_element(By.NAME, 'emailOrPhone')
        sleep(1)
        action_chains.move_to_element(email_field)
        print(account_info["email"])
        email_field.send_keys(str(account_info["email"]))
        sleep(2)

        # Fill the fullname field
        print('Filling fullname field')
        fullname_field = driver.find_element(By.NAME, 'fullName')
        action_chains.move_to_element(fullname_field)
        fullname_field.send_keys(account_info["name"])
        sleep(2)

        # Fill the username field
        print('Filling username field')
        username_field = driver.find_element(By.NAME, 'username')
        action_chains.move_to_element(username_field)
        username_field.send_keys(account_info["username"])
        sleep(2)

        # Fill the password field
        print('Filling password field')
        password_field = driver.find_element(By.NAME, 'password')
        action_chains.move_to_element(password_field)
        passW = account_info["password"]
        print(passW)
        password_field.send_keys(str(passW))
        sleep(1)

        sleep(2)

        submit = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/form/div[7]/div/button')

        action_chains.move_to_element(submit)
        sleep(2)
        submit.click()

        sleep(3)

        try:
            month_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select')
            month_button.click()
            month_button.send_keys(account_info["birthday"].split(" ")[0])
            sleep(1)
            day_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select')
            day_button.click()
            day_button.send_keys(account_info["birthday"].split(" ")[1][:-1])
            sleep(1)
            year_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select')
            year_button.click()
            year_button.send_keys(account_info["birthday"].split(" ")[2])

            sleep(2)
            next_button = driver.find_elements(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
            next_button.click()

        except Exception as e:
            print(f"Error during birthday fill: {e}")
            pass

        sleep(4)
        # After the first fill save the account account_info
        store(account_info)

        # Uncomment and implement account activation if needed
        # Activate the account
        # confirm_url = get_activation_url(account_info['email'])
        # logging.info("The confirm url is {}".format(confirm_url))
        # driver.get(confirm_url)

        driver.quit()

    def creation_config(self):
        try:
            if not self.use_local_ip_address:
                if not self.use_custom_proxy:
                    for i in range(config.Config['amount_of_account']):
                        if len(self.sockets) > 0:
                            current_socket = self.sockets.pop(0)
                            try:
                                self.createaccount(current_socket)
                            except Exception as e:
                                print(f'Error! Trying another Proxy {current_socket}')
                                self.createaccount(current_socket)

                else:
                    with open(config.Config['proxy_file_path'], 'r') as file:
                        content = file.read().splitlines()
                        for proxy in content:
                            amount_per_proxy = config.Config['amount_per_proxy']

                            if amount_per_proxy != 0:
                                print(f"Creating {amount_per_proxy} accounts for this proxy")
                                for i in range(amount_per_proxy):
                                    try:
                                        self.createaccount(proxy)
                                    except Exception as e:
                                        print(f"An error has occurred: {e}")
                            else:
                                random_number = randint(1, 20)
                                print(f"Creating {random_number} accounts for this proxy")
                                for i in range(random_number):
                                    try:
                                        self.createaccount(proxy)
                                    except Exception as e:
                                        print(f"An error has occurred: {e}")
            else:
                for i in range(config.Config['amount_of_account']):
                    try:
                        self.createaccount()
                    except Exception as e:
                        print('Error! Check if your IP might be banned')
                        self.createaccount()

        except Exception as e:
            print(f"Error in creation config: {e}")


def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()

