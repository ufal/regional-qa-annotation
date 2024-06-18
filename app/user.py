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

    def annotations(self):
        annotations = {}
        with jsonlines.open(self.data_file) as reader:
            for obj in reader:
                a = Annotation(obj)
                if a.wiki_title in annotations and a.time_saved > annotations[a.wiki_title].time_saved:
                    annotations[a.wiki_title] = Annotation(obj)
                else:
                    annotations[a.wiki_title] = Annotation(obj)
        return annotations

    def numvalid(self):
        return sum(1 for a in self.annotations().values() if not a.skipped)
    
    def numannotations(self):
        return len(self.annotations())
    
    def time_spent(self):
        # each annotation has time_saved and time_loaded. sum the differences
        # tehre is no a.time_elapsed_seconds, we do not use that
        return sum(a.time_saved - a.time_loaded for a in self.annotations().values())



        
def load_users_from_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return {name: User(name, **d) for name, d in data.items()}

