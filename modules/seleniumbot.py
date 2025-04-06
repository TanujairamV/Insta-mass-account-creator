from time import sleep
from random import randint
import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service  # Import Service
from selenium.webdriver.common.by import By  # Use By to locate elements
from selenium.webdriver.chrome.options import Options  # Use Options for setting chrome options
import requests
import re

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
        chrome_options = Options()  # Use Options instead of ChromeOptions
        if proxy != None:
            chrome_options.add_argument('--proxy-server=%s' % proxy)

        chrome_options.add_argument('window-size=1200x600')

        # Initialize Service with the path to chromedriver
        service = Service(executable_path=config.Config['chromedriver_path'])
        driver = webdriver.Chrome(service=service, options=chrome_options)  # Pass 'service' and 'options'
        print('Opening Browser')
        driver.get(self.url)
        print('Browser Opened')
        sleep(5)

        action_chains = ActionChains(driver)
        sleep(5)
        account_info = accnt.new_account()

        # fill the email value
        print('Filling email field')
        email_field = driver.find_element(By.NAME, 'emailOrPhone')
        sleep(1)
        action_chains.move_to_element(email_field)
        email_field.send_keys(str(account_info["email"]))
        sleep(2)

        # fill the fullname value
        print('Filling fullname field')
        fullname_field = driver.find_element(By.NAME, 'fullName')
        action_chains.move_to_element(fullname_field)
        fullname_field.send_keys(account_info["name"])
        sleep(2)

        # fill username value
        print('Filling username field')
        username_field = driver.find_element(By.NAME, 'username')
        action_chains.move_to_element(username_field)
        username_field.send_keys(account_info["username"])
        sleep(2)

        # fill password value
        print('Filling password field')
        password_field = driver.find_element(By.NAME, 'password')
        action_chains.move_to_element(password_field)
        passW = account_info["password"]
        password_field.send_keys(str(passW))
        sleep(2)

        submit = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/form/div[7]/div/button')
        action_chains.move_to_element(submit)
        submit.click()
        sleep(3)

        try:
            # Birthday selection part
            month_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select')
            month_button.click()
            month_value = account_info["birthday"].split(" ")[0]
            month_button.send_keys(month_value)  # Month selection
            sleep(1)

            day_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select')
            day_button.click()
            day_value = account_info["birthday"].split(" ")[1][:-1]  # Removing trailing comma
            day_button.send_keys(day_value)  # Day selection
            sleep(1)

            year_button = driver.find_element(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select')
            year_button.click()
            year_value = account_info["birthday"].split(" ")[2]
            year_button.send_keys(year_value)  # Year selection

            sleep(2)
            next_button = driver.find_elements(By.XPATH, '//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
            next_button.click()

        except Exception as e:
            print(f"Error in birthday selection: {e}")
            pass

        sleep(4)
        # After filling the account, save the account_info
        store(account_info)
        
        # Close the driver after account creation
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
                                print('Error!, Trying another Proxy {}'.format(current_socket))
                                self.createaccount(current_socket)

                else:
                    with open(config.Config['proxy_file_path'], 'r') as file:
                        content = file.read().splitlines()
                        for proxy in content:
                            amount_per_proxy = config.Config['amount_per_proxy']
                            if amount_per_proxy != 0:
                                for i in range(0, amount_per_proxy):
                                    try:
                                        self.createaccount(proxy)
                                    except Exception as e:
                                        print(f"Error: {e}")
                            else:
                                random_number = randint(1, 20)
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
                        print(f'Error: {e}')
                        self.createaccount()

        except Exception as e:
            print(f"Error: {e}")

def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()
