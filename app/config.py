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
