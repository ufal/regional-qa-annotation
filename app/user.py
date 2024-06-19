import json
import jsonlines

from app.annotation import Annotation


class User:
    def __init__(self, name, passwd, lang, data_file, role):
        self.name = name
        self.passwd = passwd
        self.lang = lang
        self.data_file = data_file
        self.role = role

    def load_annotations(self):
        annotations = {}
        with jsonlines.open(self.data_file) as reader:
            for obj in reader:
                a = Annotation(obj)
                if a.wiki_title in annotations and a.time_saved > annotations[a.wiki_title].time_saved:
                    annotations[a.wiki_title] = Annotation(obj)
                else:
                    annotations[a.wiki_title] = Annotation(obj)
        return annotations

        
def load_users_from_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return {name: User(name, **d) for name, d in data.items()}

