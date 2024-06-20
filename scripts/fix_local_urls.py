#!/usr/bin/env python3

import requests
import json
import argparse
import sys

def main(path, lang):
    with open(path, "r") as f:
        data = json.load(f)

    for d in data:
        en_link = d["en_wiki"]

        # now call wikipedia api, get langlinks, fetch the wiki title in the correct language 
        # and replace the ??_wiki field with the correct link

        en_title = en_link.split("/")[-1]
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={en_title}&prop=langlinks&format=json"
        response = requests.get(api_url)

        if response.status_code != 200:
            print(f"Failed to fetch langlinks for {en_title}", file=sys.stderr)
            continue

        pages = response.json()["query"]["pages"].values()
        if not pages:
            print(f"Failed to find {en_title}", file=sys.stderr)
            continue

        if len(pages) > 1:
            print(f"Multiple pages found for {en_title}", file=sys.stderr)
            continue

        page = list(pages)[0]

        langlinks = page.get("langlinks", [])
        for link in langlinks:
            if link["lang"] == lang:
                d[f"{lang}_wiki"] = link["*"]
                break
        else:
            print(f"Failed to find {lang} link for {en_title}", file=sys.stderr)

    json.dump(data, sys.stdout, indent=4)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str)    
    parser.add_argument("language", type=str)
    args = parser.parse_args()
    main(args.path, args.language)