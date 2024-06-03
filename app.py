#!/usr/bin/env python3

import argparse
import requests
import hashlib

from app.config import load_user_config

from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)


def get_random_article(lng):
    url = f"https://{lng}.wikipedia.org/api/rest_v1/page/random/summary"
    response = requests.get(url)
    return response.json().get("title")


@app.route("/")
def index():
    username = request.cookies.get("username")
    if username is not None:
        random_title = get_random_article(users[username]["lang"])
        return redirect(url_for("annotate_wiki", wiki_title=random_title))

    else:
        return redirect(url_for("login"))


@app.route("/annotate/<string:wiki_title>")
def annotate_wiki(wiki_title):
    username = request.cookies.get("username")
    if username is None:
        return redirect(url_for("login"))

    return render_template("annotate.html",
                           username=username,
                           wiki_lang=users[username]["lang"],
                           wiki_title=wiki_title,
                           question="",
                           answer="")


@app.route("/annotate", methods=["POST"])
def annotate():
    username = request.cookies.get("username")
    if username is None:
        return redirect(url_for("login"))

    if "skip" in request.form:
        # redirect to random article
        random_title = get_random_article(users[username]["lang"])
        return redirect(url_for("annotate_wiki", wiki_title=random_title))

    wiki_title = request.form["wiki_title"]
    wiki_lang = request.form["wiki_lang"]
    question = request.form["question"].replace("\n", " ").strip()
    answer = request.form["answer"].replace("\n", " ").strip()

    contains_image_info = request.form.get("imgurl") is None
    if contains_image_info:
        image_url = request.form["imgurl"].strip()
        image_question = request.form["img-question"].replace("\n", " ").strip()
        image_answer = request.form["img-answer"].replace("\n", " ").strip()
    else:
        image_url = "null"
        image_question = "null"
        image_answer = "null"

    with open(users[username]["logfile"], "a") as f:
        f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
            wiki_lang, wiki_title,
            question.replace('\t', ' '), answer.replace('\t', ' '),
            image_url, image_question.replace('\t', ' '), image_answer.replace('\t', ' ')))

    # redirect to random article
    random_title = get_random_article(users[username]["lang"])
    return redirect(url_for("annotate_wiki", wiki_title=random_title))


@app.route("/wiki/<string:wiki_title>")
def wiki(wiki_title):
    # we are including texts from wiki - we can intercept this route to switch
    # articles
    return redirect(url_for("annotate_wiki", wiki_title=wiki_title))


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(
            request.form["password"].encode()).hexdigest()

        if username in users and users[username]["passwd"] == password:
            random_title = get_random_article(users[username]["lang"])
            response = redirect(url_for("annotate_wiki", wiki_title=random_title))
            response.set_cookie("username", username)
            return response
        else:
            return render_template(
                "index.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    response = redirect(url_for("login"))
    response.set_cookie("username", "", expires=0)
    return response


if __name__ == "__main__":
    users = load_user_config("config/users.tsv")
    app.run(host="0.0.0.0", debug=True, port=8080)
