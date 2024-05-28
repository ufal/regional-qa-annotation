
def load_user_config(path):

    users = {}
    with open(path) as f:
        for line in f:
            user, passwd, language, logfile = line.strip().split("\t", maxsplit=4)
            users[user] = {"passwd": passwd, "logfile": logfile, "lang": language}

    return users
