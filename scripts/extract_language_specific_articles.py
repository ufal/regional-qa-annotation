#!/usr/bin/env python3

import requests
import json
import sys
import argparse
import time
from tqdm import tqdm

# Wikimedia rejects requests without a descriptive User-Agent (T400119).
HEADERS = {"User-Agent": "regional-qa-annotation/0.1 (https://github.com/ufal/regional-qa-annotation)"}

def get_json(url, params, retries=6):
    # The API occasionally returns a broken response (e.g. valid JSON with
    # garbage appended) or a 5xx; retry with exponential backoff.
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=60)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"Request failed ({e}), retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)


def query(request, lang):
    request["action"] = "query"
    request["format"] = "json"
    last_continue = {}
    while True:
        req = request.copy()
        req.update(last_continue)
        result = get_json(f"https://{lang}.wikipedia.org/w/api.php", req)
        if "error" in result:
            raise Exception(result["error"])
        if "warnings" in result:
            print(result["warnings"], file=sys.stderr)
        yield result
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
        for page in result.get("query", {}).get("allpages", []):
            print(page["title"])


def extract_with_allowed(lang, allowed):
    # Articles whose langlinks all point to languages in `allowed` (no
    # langlinks at all also counts). Useful when several languages share a
    # region, e.g. Bokmål articles that exist only in Nynorsk or Northern Sami.
    # The API cannot filter on this, so we fetch the langlinks of all pages.

    request = {
        "generator": "allpages",
        "gaplimit": "max",
        "gapfilterredir": "nonredirects",
        "gapnamespace": 0,
        "prop": "langlinks",
        "lllimit": "max",
    }

    # Article count from site statistics, only used as the progress bar total.
    stats = next(query({"meta": "siteinfo", "siprop": "statistics"}, lang))
    progress = tqdm(total=stats["query"]["statistics"]["articles"], unit="page")

    # Langlinks of one batch of pages may span several responses; the batch is
    # complete once the response carries "batchcomplete".
    batch = {}
    kept = 0
    for result in query(request, lang):
        for page in result.get("query", {}).get("pages", {}).values():
            title, langs = batch.setdefault(page["pageid"], (page["title"], set()))
            langs.update(link["lang"] for link in page.get("langlinks", []))

        if "batchcomplete" in result:
            for title, langs in batch.values():
                if langs <= allowed:
                    print(title)
                    kept += 1
            progress.update(len(batch))
            progress.set_postfix(kept=kept)
            batch = {}
    progress.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract language specific articles from Wikipedia')
    parser.add_argument('lang', type=str, help='Language code of the Wikipedia')
    parser.add_argument('--allowed', type=str, default=None,
                        help='Comma-separated langlink codes an article may link to and still count as local '
                             '(e.g. "nn,se" for Bokmål). Without it, only articles with no langlinks are kept.')
    args = parser.parse_args()
    if args.allowed is None:
        extract(args.lang)
    else:
        extract_with_allowed(args.lang, set(args.allowed.split(",")))
