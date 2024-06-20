import json


def load_wiki_articles(path, language):
    # loads a json file which looks like this:
    # [
    #   {
    #     "en_wiki": "http://en.wikipedia.org/wiki/Pote\u010d",
    #     "cs_wiki": "http://cs.wikipedia.org/wiki/Pote\u010d",
    #     "wiki_id": 24130327,
    #     "topics": [
    #       "geo",
    #       "generic"
    #     ]
    #   },
    # ... and so on
    # returns a list of wiki titles extracted from the ??_wiki (depending on the language parameter -- in this case it would be "cs")
    # wiki title is the thing that follows the wiki/ in the URL
    # 
    # also convert the escaped unicode characters to actual unicode characters

    with open(path, "r") as f:
        data = json.load(f)
    return [d[f"{language}_wiki"].split("/")[-1] for d in data]

