#!/usr/bin/env python3

import argparse
import json
import tarfile
import jsonlines
import urllib.parse
import sys

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

  output_html = open(args.output, "w")
  output_tsv = open(args.tsv_output, "w")

  print("reading...", end="", flush=True, file=sys.stderr)

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

  print("done", file=sys.stderr)

  print("<html><head><meta charset='utf-8'></head><body>", file=output_html)

  index = 1

  for user in annotations:
    print(f"{user}...", end="", flush=True, file=sys.stderr)

    if user in ["admin", "test"]:
      continue

    for wiki_title, annotation in annotations[user].items():
      if annotation.skipped:
        continue

      if annotation.wiki_lang != args.lang:
        continue

      if annotation.img_skipped:
        continue

      img_url = annotation.img_url
      img_q = " ".join(annotation.img_question.strip().split())
      img_a = " ".join(annotation.img_answer.strip().split())
      img_q_en = " ".join(annotation.img_question_en.strip().split())
      img_a_en = " ".join(annotation.img_answer_en.strip().split())
      wiki_url = f"https://{args.lang}.wikipedia.org/wiki/" + urllib.parse.quote_plus(annotation.wiki_title)

      print(f"<h2><a href=\"{wiki_url}\">{index} {wiki_title}</a></h2>", file=output_html)
      print(f"<img src='{img_url}'><br>", file=output_html)
      print(f"<b>Q:</b> {img_q} <i>{img_q_en}</i> <br>", file=output_html)
      print(f"<b>A:</b> {img_a} <i>{img_a_en}</i><br>", file=output_html)
      print("<hr>", file=output_html)

      print(f"{index}\t{user}\t{wiki_title}\t{img_q}\t{img_a}\t{img_q_en}\t{img_a_en}\t{wiki_url}", file=output_tsv)

      index += 1

    print("done", file=sys.stderr)

  print("</body></html>", file=output_html)

if __name__ == "__main__":
  print("hello! ", file=sys.stderr, end="", flush=True)

  parser = argparse.ArgumentParser(description='Export data from backup')
  parser.add_argument('backup', type=str, help='path to backup file')
  parser.add_argument('--lang', type=str, default="cs", help='language of the annotations')
  parser.add_argument('--output', type=str, default="output.html", help='output file')
  parser.add_argument('--tsv_output', type=str, default="output.tsv", help='output file')
  args = parser.parse_args()

  print("args loadded", file=sys.stderr, flush=True)

  main(args)
