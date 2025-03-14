#!/usr/bin/env python3


import argparse
import json
import tarfile


def main():
    parser = argparse.ArgumentParser(description='Get stats from backup')
    parser.add_argument(
        'backup', nargs="+", type=str, help='path to backup file(s)')
    parser.add_argument(
        '--languages', type=str, nargs='+',
        help='languages to filter by', default=["cs", "sk", "uk"])
    args = parser.parse_args()

    for backup in args.backup:
        text_question_count = {lng: 0 for lng in args.languages}
        image_question_count = {lng: 0 for lng in args.languages}

        with tarfile.open(backup, 'r') as tar:
            members = tar.getmembers()
            for member in members:
                if not member.isfile():
                    continue
                lng = None
                text_questions = set()
                image_questions = set()
                for line in tar.extractfile(member):
                    log_item = json.loads(line)
                    if lng is None:
                        lng = log_item['wiki_lang']
                        if lng not in args.languages:
                            break
                    else:
                        assert lng == log_item['wiki_lang']
                    if log_item['skipped']:
                        continue
                    text_questions.add(log_item['wiki_title'])
                    if not log_item['img_skipped']:
                        image_questions.add(log_item['wiki_title'])
                if lng is None:
                    continue
                text_question_count[lng] += len(text_questions)
                image_question_count[lng] += len(image_questions)

        print(backup, end="\t")
        print("\t".join(f"{lng}: {text_question_count[lng]}/{image_question_count[lng]}"
                        for lng in args.languages))




if __name__ == '__main__':
    main()
