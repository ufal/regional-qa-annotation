#!/usr/bin/env python3

import argparse
import requests
import hashlib
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

# basic passwd dict with sha256 hashed passwords
passwd = {"admin": hashlib.sha256("ahoj123".encode()).hexdigest(),
          "user": hashlib.sha256("helohelo".encode()).hexdigest()}

# example data: URL, Question, Answer (the Q and A are empty by default)
# data = {"cs": [("Německo", "Jaké je hlavní město Německa?", "Berlín")],
#         "en": [
#     ("Germany", "What is the capital of Germany?", "Berlin"),
#     ("United_States", "What is the capital of the United States?", "Washington, D.C."),
#     ("Canada", "What is the capital of Canada?", "Ottawa"),
#     ("Czech_Republic", "What is the capital of the Czech Republic?", "Prague")]}

language = "cs"
annotations = []  # this is saved every time it is updated

def get_random_article():
    url = "https://{}.wikipedia.org/api/rest_v1/page/random/summary".format(language)
    response = requests.get(url)
    return response.json().get("title")


@app.route("/")
def index():
    # check if logged in
    username = request.cookies.get("username")
    if username is not None:
        random_title = get_random_article()
        return redirect(url_for("annotate_wiki", wiki_title=random_title))
    else:
        # redirect to login page
        return redirect(url_for("login"))


# annotate route with wiki title as id
@app.route("/annotate/<string:wiki_title>")
def annotate_wiki(wiki_title):
    # check if logged in
    username = request.cookies.get("username")

    if username is None:
        return redirect(url_for("login"))

    return render_template("annotate.html",
                           username=username,
                           wiki_lang=language,
                           wiki_title=wiki_title,
                           question="",
                           answer="")


@app.route("/annotate", methods=["POST"])
def annotate():
    # check if logged in
    username = request.cookies.get("username")

    if username is None:
        return redirect(url_for("login"))

    # was it the skip button?
    if "skip" in request.form:
        # redirect to random article
        random_title = get_random_article()
        return redirect(url_for("annotate_wiki", wiki_title=random_title))

    wiki_title = request.form["wiki_title"]
    wiki_lang = request.form["wiki_lang"]
    question = request.form["question"].replace("\n", " ").strip()
    answer = request.form["answer"].replace("\n", " ").strip()

    with open("data.tsv", "a") as f:
        # make sure to escape chars
        f.write("{}\t{}\t{}\t{}\n".format(wiki_lang, wiki_title, question.replace('\t', ' '), answer.replace('\t', ' ')))

    # redirect to random article
    random_title = get_random_article()
    return redirect(url_for("annotate_wiki", wiki_title=random_title))




@app.route("/wiki/<string:wiki_title>")  # redirect to annotate_wiki with wiki title as id
def wiki(wiki_title):
    return redirect(url_for("annotate_wiki", wiki_title=wiki_title))


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in passwd and passwd[username] == hashlib.sha256(password.encode()).hexdigest():
            # redirect to random article
            random_title = get_random_article()
            response = redirect(url_for("annotate", wiki_title=random_title))
            response.set_cookie("username", username)
            return response
        else:
            return render_template("index.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    response = redirect(url_for("login"))
    response.set_cookie("username", "", expires=0)
    return response


def main(args):
    language = args.lang
    app.run(host="0.0.0.0", port=args.port, debug=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--lang", type=str, default="cs", required=True)
    parser.add_argument("--data", type=str, default="data.csv")
    args = parser.parse_args()
    main(args)
