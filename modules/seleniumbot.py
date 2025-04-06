from time import sleep
from random import randint
import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        chrome_options = webdriver.ChromeOptions()
        if proxy != None:
            chrome_options.add_argument('--proxy-server=%s' % proxy)

        # Set user-agent and window size
        chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36"')
        chrome_options.add_argument('window-size=1200x600')

        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options, executable_path=config.Config['chromedriver_path'])
        print('Opening Browser')
        driver.get(self.url)
        print('Browser Opened')
        sleep(5)

        action_chains = ActionChains(driver)
        sleep(5)
        account_info = accnt.new_account()

        # Fill the email field
        print('Filling email field')
        email_field = driver.find_element_by_name('emailOrPhone')
        sleep(1)
        action_chains.move_to_element(email_field)
        email_field.send_keys(str(account_info["email"]))
        sleep(2)

        # Fill the fullname field
        print('Filling fullname field')
        fullname_field = driver.find_element_by_name('fullName')
        action_chains.move_to_element(fullname_field)
        fullname_field.send_keys(account_info["name"])
        sleep(2)

        # Fill the username field
        print('Filling username field')
        username_field = driver.find_element_by_name('username')
        action_chains.move_to_element(username_field)
        username_field.send_keys(account_info["username"])
        sleep(2)

        # Fill the password field
        print('Filling password field')
        password_field = driver.find_element_by_name('password')
        action_chains.move_to_element(password_field)
        passW = account_info["password"]
        password_field.send_keys(str(passW))
        sleep(2)

        # Click the submit button using WebDriverWait to ensure it's clickable
        submit_button_xpath = '//*[@id="react-root"]/section/main/div/div/div[1]/div/form/div[7]/div/button'
        submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
        )
        submit.click()

        sleep(3)

        try:
            # Handle birthday selection
            month_button = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select')
            month_button.click()
            month_button.send_keys(account_info["birthday"].split(" ")[0])
            sleep(1)
            day_button = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select')
            day_button.click()
            day_button.send_keys(account_info["birthday"].split(" ")[1][:-1])
            sleep(1)
            year_button = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select')
            year_button.click()
            year_button.send_keys(account_info["birthday"].split(" ")[2])

            sleep(2)
            next_button = driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
            next_button.click()

        except Exception as e:
            print(f"Error in filling birthday details: {e}")

        sleep(4)
        # Save the account information after the first step
        store(account_info)

        driver.close()

    def creation_config(self):
        try:
            if not self.use_local_ip_address:
                if not self.use_custom_proxy:
                    for i in range(0, config.Config['amount_of_account']):
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
                                print(f"Creating {amount_per_proxy} amount of users for this proxy")
                                for i in range(0, amount_per_proxy):
                                    try:
                                        self.createaccount(proxy)
                                    except Exception as e:
                                        print(f"An error has occurred: {e}")
                            else:
                                random_number = randint(1, 20)
                                print(f"Creating {random_number} amount of users for this proxy")
                                for i in range(0, random_number):
                                    try:
                                        self.createaccount(proxy)
                                    except Exception as e:
                                        print(f"Error: {e}")
            else:
                for i in range(0, config.Config['amount_of_account']):
                    try:
                        self.createaccount()
                    except Exception as e:
                        print(f'Error! Check if your IP might be banned: {e}')
                        self.createaccount()

        except Exception as e:
            print(f"Error in creation config: {e}")

def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()
