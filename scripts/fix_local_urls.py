#!/usr/bin/env python3
""" Retrieve target language URLs given a JSON with English URLs. """

import requests
import json
import argparse
import sys
from tqdm import tqdm



def query(request):
    request["action"] = "query"
    request["format"] = "json"
    last_continue = {}
    while True:
        req = request.copy()
        req.update(last_continue)
        result = requests.get("https://en.wikipedia.org/w/api.php", params=req).json()
        if "error" in result:
            raise Exception(result["error"])
        if "warnings" in result:
            print(result["warnings"], file=sys.stderr)
        if "query" in result:
            yield result["query"]
        if "continue" not in result:
            break
        last_continue = result["continue"]


def process_batch(batch, lang):
    lang_links = {title: None for title in batch}
        
    titles = "|".join(batch)
    for result in query({"titles": titles, "prop": "langlinks", "lllimit": "max", "llprop": "url", "redirects": 1}):
        pages = result["pages"].values()
        
        normalized = result.get("normalized", [])
        redirects = result.get("redirects", [])

        normalized_mapping_rev = {n["to"]: n["from"] for n in normalized}
        redirects_mapping_rev = {r["to"]: r["from"] for r in redirects}

        for page in pages:
            pagetitle_normalized_redirected = page["title"]
            if pagetitle_normalized_redirected in redirects_mapping_rev:
                pagetitle_normalized = redirects_mapping_rev[pagetitle_normalized_redirected]
            else:
                pagetitle_normalized = pagetitle_normalized_redirected

            if pagetitle_normalized in normalized_mapping_rev:
                pagetitle = normalized_mapping_rev[pagetitle_normalized]
            else:
                pagetitle = pagetitle_normalized
            
            if pagetitle not in lang_links:
                print(f"Unknown pagetitle: {pagetitle}", file=sys.stderr)
                print(f"normalized: {pagetitle_normalized}", file=sys.stderr)
                print(f"redirected: {pagetitle_normalized_redirected}", file=sys.stderr)

            langlinks = page.get("langlinks", [])

            for link in langlinks:
                if link["lang"] == lang:
                    url = link["url"]
                    lang_links[pagetitle] = url
                    break


    for title, url in lang_links.items():
        if url is None:
            print(f"Could not find {lang} link for {title}", file=sys.stderr)
        else:
            print(f"{url}")

    


def main(path, lang):

    with open(path, "r") as f:
        data = json.load(f)

    batch_size = 50  # this is the maximum mediawiki allows
    batch = []

    for d in tqdm(data):
        en_link = d["en_wiki"]

        # now call wikipedia api, get langlinks, fetch the wiki title in the correct language 
        # and replace the ??_wiki field with the correct link
        
        en_title = en_link.split("/")[-1]
        batch.append(en_title)
        
        if len(batch) == batch_size:
            process_batch(batch, lang)
            batch = []

    if batch:
        process_batch(batch, lang)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str)    
    parser.add_argument("language", type=str)
    args = parser.parse_args()
    main(args.path, args.language)