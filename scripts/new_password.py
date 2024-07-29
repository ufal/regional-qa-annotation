#!/usr/bin/env python3

import getpass
import hashlib

password = None
while password is None:
    password_1 = getpass.getpass("Enter your password: ")
    password_2 = getpass.getpass("Re-enter your password: ")
    if password_1 == password_2:
        password = password_1
    else:
        print("Passwords do not match. Please try again.")

hash = hashlib.sha256(password.encode()).hexdigest()
print(hash)