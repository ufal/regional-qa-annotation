#!/usr/bin/env python3

import requests
import json
import sys
import argparse

def query(request, lang):
    request["action"] = "query"
    request["format"] = "json"
    last_continue = {}
    while True:
        req = request.copy()
        req.update(last_continue)
        result = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params=req).json()
        if "error" in result:
            raise Exception(result["error"])
        if "warnings" in result:
            print(result["warnings"], file=sys.stderr)
        if "query" in result:
            yield result["query"]
        if "continue" not in result:
            break
        last_continue = result["continue"]


def extract(lang):

    request = {
        "list": "allpages",
        "aplimit": "max",  # as many as possible
        "apfilterredir": "nonredirects",  # only non-redirects
        "apfilterlanglinks": "withoutlanglinks",  # only articles without langlinks - those are *truly* local
        "apnamespace": 0  # only main namespace
    }

    for result in query(request, lang):
        for page in result["allpages"]:
            print(page["title"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract language specific articles from Wikipedia')
    parser.add_argument('lang', type=str, help='Language code of the Wikipedia')
    args = parser.parse_args()
    extract(args.lang)
