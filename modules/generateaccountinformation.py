""" author: feezyhendrix

    this module contains followers generation
"""

import random
import mechanicalsoup
import string
import logging

from .config import Config
from .getIdentity import getRandomIdentity

# Generating a username
def username(identity):
    n = str(random.randint(1, 99))
    name = str(identity).lower().replace(" ", "")
    username = name + n
    logging.info("Username: {}".format(username))
    return username

# Generate a strong password
def generatePassword(length=12):
    while True:
        password_characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(password_characters) for _ in range(length))

        # Ensure password meets criteria
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in string.punctuation for c in password)):
            return password

# Generate email from username
def genEmail(username):
    return username + "@" + str(Config["email_domain"])

# Build the full account object
def new_account():
    account_info = {}
    identity, gender, birthday = getRandomIdentity(country=Config["country"])
    account_info["name"] = identity
    account_info["username"] = username(account_info["name"])
    account_info["password"] = generatePassword()
    account_info["email"] = genEmail(account_info["username"])
    account_info["gender"] = gender
    account_info["birthday"] = birthday
    return account_info
