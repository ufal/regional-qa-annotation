#!/usr/bin/env python3

import argparse
import json
import tarfile
import jsonlines
import urllib.parse

from app.annotation import Annotation

def load_annotations(fh):
  annotations = {}

  with jsonlines.Reader(fh) as reader:
    for obj in reader:
      a = Annotation(obj)
      if a.wiki_title in annotations and a.time_saved > annotations[a.wiki_title].time_saved:
        annotations[a.wiki_title] = Annotation(obj)
      else:
        annotations[a.wiki_title] = Annotation(obj)

  return annotations


def main(args):

  with tarfile.open(args.backup, "r") as tar:
    members = tar.getmembers()
    annotations = {}
    for member in members:
      if not member.isfile():
        continue

      if not member.name.endswith(".jsonl"):
        continue

      username = member.name[:-6]

      annotations[username] = load_annotations(tar.extractfile(member))

  for user in annotations:
    if user in ["admin", "test"]:
      continue

    for wiki_title, annotation in annotations[user].items():
      if annotation.skipped:
        continue

      if annotation.wiki_lang != args.lang:
        continue

      q = " ".join(annotation.question.strip().split())
      a = " ".join(annotation.answer.strip().split())
      qen = " ".join(annotation.question_en.strip().split())
      aen = " ".join(annotation.answer_en.strip().split())
      has_img = "yes" if not annotation.img_skipped else "no"
      wiki_url = f"https://{args.lang}.wikipedia.org/wiki/" + urllib.parse.quote_plus(annotation.wiki_title)


      print(f"{user}\t{wiki_title}\t{q}\t{a}\t{qen}\t{aen}\t{has_img}\t{wiki_url}")





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export data from backup')
    parser.add_argument('backup', type=str, help='path to backup file')
    parser.add_argument('--lang', type=str, default="cs", help='language of the annotations')
    args = parser.parse_args()

    main(args)
