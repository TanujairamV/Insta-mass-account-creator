import logging
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from modules.generateaccountinformation import new_account
from modules.storeusername import store
import modules.config as config

MAIL_TM_BASE = "https://api.mail.tm"

def create_mail_tm_account():
    domain = requests.get(f"{MAIL_TM_BASE}/domains").json()["hydra:member"][0]["domain"]
    email = f"{int(time.time())}@{domain}"
    password = "instab0tPass123"

    response = requests.post(f"{MAIL_TM_BASE}/accounts", json={"address": email, "password": password})
    if response.status_code != 201:
        raise Exception(f"Failed to create temp email: {response.text}")
    token_resp = requests.post(f"{MAIL_TM_BASE}/token", json={"address": email, "password": password})
    token = token_resp.json()["token"]
    return email, password, token

def get_confirmation_code(token):
    headers = {"Authorization": f"Bearer {token}"}
    logging.info("[INFO] Waiting for confirmation code...")
    for _ in range(60):  # Wait max 60 seconds
        resp = requests.get(f"{MAIL_TM_BASE}/messages", headers=headers).json()
        if resp["hydra:member"]:
            msg_id = resp["hydra:member"][0]["id"]
            msg = requests.get(f"{MAIL_TM_BASE}/messages/{msg_id}", headers=headers).json()
            code = extract_code_from_email(msg["text"])
            if code:
                return code
        time.sleep(2)
    raise TimeoutError("Confirmation code not received in time.")

def extract_code_from_email(text):
    import re
    match = re.search(r'(\d{6})', text)
    return match.group(1) if match else None

def run():
    logging.basicConfig(level=logging.INFO)
    account_info = new_account()
    email, email_password, token = create_mail_tm_account()
    account_info["email"] = email

    logging.info(f"[INFO] Generated temp email: {email}")

    # Setup WebDriver
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(config.Config["chromedriver_path"]), options=options)
    wait = WebDriverWait(driver, 20)

    try:
        logging.info("Opening Instagram signup page...")
        driver.get("https://www.instagram.com/accounts/emailsignup/")

        wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone"))).send_keys(email)
        driver.find_element(By.NAME, "fullName").send_keys(account_info["name"])
        driver.find_element(By.NAME, "username").send_keys(account_info["username"])
        driver.find_element(By.NAME, "password").send_keys(account_info["password"])
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Wait for DOB input to appear
        time.sleep(3)
        birthday = account_info["birthday"].split(" ")
        wait.until(EC.presence_of_element_located((By.XPATH, '//select[@title="Month:"]'))).send_keys(birthday[0])
        driver.find_element(By.XPATH, '//select[@title="Day:"]').send_keys(birthday[1][:-1])
        driver.find_element(By.XPATH, '//select[@title="Year:"]').send_keys(birthday[2])
        driver.find_element(By.XPATH, '//button[text()="Next"]').click()

        # Wait for confirmation code input page
        logging.info(f"[INFO] Waiting for confirmation code at {email}...")
        code = get_confirmation_code(token)
        logging.info(f"[INFO] Got code: {code}")

        wait.until(EC.presence_of_element_located((By.NAME, 'email_confirmation_code'))).send_keys(code)
        driver.find_element(By.XPATH, '//button[text()="Next"]').click()

        # Store credentials
        store(account_info)
        logging.info(f"[SUCCESS] Account created: {account_info['username']}")
        logging.info(f"Username: {account_info['username']}")
        logging.info(f"Password: {account_info['password']}")

        input("Press ENTER to close browser...")  # keeps browser open for inspection

    except Exception as e:
        logging.error(f"[ERROR] Something went wrong: {e}")
    # finally:
    #     driver.quit()  # Commented out to keep browser open

if __name__ == "__main__":
    run()
