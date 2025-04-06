import logging
import time
from random import randint
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import modules.config as config
import modules.generateaccountinformation as accnt
from modules.storeusername import store
from modules.tempmail import TempMailClient

logging.basicConfig(level=logging.INFO)

class AccountCreator():
    def __init__(self, use_custom_proxy, use_local_ip_address):
        self.use_custom_proxy = use_custom_proxy
        self.use_local_ip_address = use_local_ip_address

    def human_typing(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(0.1)

    def createaccount(self, proxy=None):
        options = Options()
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36')
        options.add_argument('window-size=1200x600')

        service = Service(executable_path=config.Config['chromedriver_path'])
        driver = webdriver.Chrome(service=service, options=options)

        try:
            logging.info("Opening Browser")
            driver.get('https://www.instagram.com/accounts/emailsignup/')
            wait = WebDriverWait(driver, 20)
            action_chains = ActionChains(driver)

            tm = TempMailClient()
            email = tm.create_account()
            account_info = accnt.new_account(email=email)
            logging.info(f"Email: {email}")
            logging.info(f"Gender: {account_info['gender']}")
            logging.info(f"Url generated: {account_info['url']}")
            logging.info(f"Birthday: {account_info['birthday']}")
            logging.info(f"Username: {account_info['username']}")

            # Form filling with human typing
            email_field = wait.until(EC.presence_of_element_located((By.NAME, 'emailOrPhone')))
            self.human_typing(email_field, str(account_info["email"]))
            time.sleep(1)

            fullname_field = driver.find_element(By.NAME, 'fullName')
            self.human_typing(fullname_field, account_info["name"])
            time.sleep(1)

            username_field = driver.find_element(By.NAME, 'username')
            self.human_typing(username_field, account_info["username"])
            time.sleep(3)

            password_field = driver.find_element(By.NAME, 'password')
            self.human_typing(password_field, str(account_info["password"]))
            time.sleep(2)

            # Check if username is valid (error label)
            error_check = driver.find_elements(By.XPATH, '//p[@id="ssfErrorAlert"]')
            if error_check:
                print("[ERROR] Username or input not valid. Skipping...")
                driver.quit()
                return

            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
            action_chains.move_to_element(submit_button).click().perform()
            time.sleep(5)

            # Birthday form
            birthday = account_info["birthday"].split(" ")
            try:
                logging.info("Filling birthday details")
                month_select = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@title="Month:"]')))
                month_select.send_keys(birthday[0])
                time.sleep(1)

                day_select = driver.find_element(By.XPATH, '//select[@title="Day:"]')
                day_select.send_keys(birthday[1][:-1])
                time.sleep(1)

                year_select = driver.find_element(By.XPATH, '//select[@title="Year:"]')
                year_select.send_keys(birthday[2])
                time.sleep(1)

                next_button = driver.find_element(By.XPATH, '//button[text()="Next"]')
                next_button.click()
                time.sleep(3)
            except Exception as e:
                print(f"[WARNING] Skipping birthday selection: {e}")

            # Wait for confirmation code from mail.tm
            logging.info("[INFO] Waiting for confirmation code...")
            code = tm.wait_for_code(email)
            if not code:
                logging.error("[ERROR] No code received")
                driver.quit()
                return

            confirmation_input = wait.until(EC.presence_of_element_located((By.NAME, 'email_confirmation_code')))
            confirmation_input.send_keys(code)
            time.sleep(2)

            confirm_button = driver.find_element(By.XPATH, '//button[text()="Next"]')
            confirm_button.click()
            time.sleep(5)

            store(account_info)
            print(f"[SUCCESS] Account created: {account_info['username']} | Password: {account_info['password']}")

        except Exception as e:
            print(f"[FATAL ERROR] {e}")
        finally:
            pass  # Change to driver.quit() if you don't want to keep the browser open

    def creation_config(self):
        try:
            for _ in range(config.Config['amount_of_account']):
                try:
                    self.createaccount()
                except Exception as e:
                    print(f"[ERROR] Something went wrong: {e}")
        except Exception as e:
            print(f"[FATAL ERROR] {e}")

def runbot():
    account = AccountCreator(config.Config['use_custom_proxy'], config.Config['use_local_ip_address'])
    account.creation_config()
