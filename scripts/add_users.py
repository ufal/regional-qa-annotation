#!/usr/bin/env python3
"""Interactively add annotators who share one language.

Run from the repository root (the app uses paths relative to it):

    python3 scripts/add_users.py

Asks for the language once, then for usernames until an empty line. Each user
gets a generated password (6 letters + 2 digits), an entry in config/users.json
and an empty data/<username>.jsonl. Passwords are printed at the end; only
their hashes are stored.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import USERS_FILE, WIKI_LANGS

# No l/o and 0/1 so that passwords can be read out or copied from paper.
LETTERS = "abcdefghijkmnpqrstuvwxyz"
DIGITS = "23456789"
USERNAME_RE = re.compile(r"^[a-z0-9_]+$")


def generate_password():
    return ("".join(secrets.choice(LETTERS) for _ in range(6))
            + "".join(secrets.choice(DIGITS) for _ in range(2)))


def ask_lang():
    while True:
        lang = input(f"Language for all new users {WIKI_LANGS}: ").strip()
        if lang in WIKI_LANGS:
            return lang
        print(f"'{lang}' is not in WIKI_LANGS in main.py.")


def ask_usernames(existing):
    new = []
    print("Usernames (e.g. jan_novak), empty line to finish:")
    while True:
        name = input("> ").strip()
        if not name:
            return new
        if not USERNAME_RE.match(name):
            print("Use only lowercase letters, digits and underscores.")
        elif name in existing or name in new:
            print(f"'{name}' already exists.")
        elif os.path.exists(f"data/{name}.jsonl"):
            print(f"data/{name}.jsonl already exists, pick another name.")
        else:
            new.append(name)


def main(role):
    with open(USERS_FILE) as f:
        users = json.load(f)

    lang = ask_lang()
    names = ask_usernames(users)
    if not names:
        print("Nothing to do.")
        return

    passwords = {name: generate_password() for name in names}
    print(f"\nAbout to add {len(names)} user(s) with lang={lang}, role={role}:")
    for name in names:
        print(f"  {name}")
    if input("Write them? [y/N] ").strip().lower() != "y":
        print("Aborted, nothing written.")
        return

    backup = f"{USERS_FILE}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
    shutil.copy2(USERS_FILE, backup)

    for name in names:
        users[name] = {
            "passwd": hashlib.sha256(passwords[name].encode()).hexdigest(),
            "lang": lang,
            "data_file": f"data/{name}.jsonl",
            "role": role,
        }
        # load_annotations() fails on a missing file, so start with an empty one.
        open(f"data/{name}.jsonl", "a").close()

    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)
    os.replace(tmp, USERS_FILE)

    print(f"\nDone (previous config backed up to {backup}). Credentials:")
    for name in names:
        print(f"{name}\t{passwords[name]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--role", default="user", choices=["user", "admin"])
    args = parser.parse_args()
    main(args.role)
