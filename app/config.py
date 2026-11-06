import json
import re
from urllib.parse import unquote


def normalize_title(title):
    # wiki normalization does more stuff but we only need this because the
    # titles are extracted from wiki itself.
    return title.replace(" ", "_")


def load_wiki_titles_from_urls(path, urlencoded=True):
    titles = []

    with open(path) as f:
        for url in f:
            if urlencoded:
                url = unquote(url)

            url = url.rstrip("\r\n")
            title = re.sub("^.*wikipedia.org/wiki/", "", url)
            titles.append(title)

    return titles


def load_wiki_titles(path, normalized=False):
    urls = []
    with open(path) as f:
        for title in f:
            if not normalized:
                title = normalize_title(title)
            urls.append(title.rstrip("\r\n"))
    return urls


# The country each Wikipedia language stands for in this project. Used both in
# the annotation instructions and in the machine-translation prompt, which tells
# the model which country the question is about.
LANG_COUNTRY = {
    "cs": "Czech Republic",
    "sk": "Slovakia",
    "uk": "Ukraine",
    "no": "Norway",
    "nn": "Norway",
    "hr": "Croatia",
    "sl": "Slovenia",
    "pl": "Poland",
    "et": "Estonia",
    "vro": "Estonia",
}


def lang_country(lang):
    return LANG_COUNTRY.get(lang.lower(), "")
