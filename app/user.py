import json


class User:
    def __init__(self, name, passwd, lang, data_file, role):
        self.name = name
        self.passwd = passwd
        self.lang = lang
        self.data_file = data_file
        self.role = role


def load_users_from_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return {name: User(name, **d) for name, d in data.items()}

