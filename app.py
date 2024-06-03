#!/usr/bin/env python3
import hashlib
import jsonlines
import requests
import time
from flask import Flask, render_template, request, redirect, url_for
from functools import wraps

from app.config import load_user_config
from app.annotation import Annotation

app = Flask(__name__)


def get_random_article(lng):
    url = f"https://{lng}.wikipedia.org/api/rest_v1/page/random/summary"
    response = requests.get(url)
    return response.json().get("title")

def logged_in(f):
    @wraps(f)
    def fun(*args, **kwargs):
        if request.cookies.get("username") is not None:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))
    return fun


@app.route("/")
@logged_in
def index():
    # todo here might be some sort of dashboard
    return redirect(url_for("annotate_random"))


@app.route("/annotate/<string:wiki_title>")
@logged_in
def annotate_wiki(wiki_title):
    username = request.cookies.get("username")
    return render_template(
        "annotate.html",
        username=username,
        wiki_lang=users[username]["lang"],
        wiki_title=wiki_title,
        random_page=False,
        timestamp=time.time(),
        question="",
        answer="")

@app.route("/annotate", methods=["GET"])
@logged_in
def annotate_random():
    username = request.cookies.get("username")
    random_title = get_random_article(users[username]["lang"])
    return render_template(
        "annotate.html",
        username=username,
        wiki_lang=users[username]["lang"],
        wiki_title=random_title,
        random_page=True,
        timestamp=time.time(),
        question="",
        answer="")

@app.route("/linkclick", methods=["POST"])
@logged_in
def linkclick():
    username = request.cookies.get("username")
    anot = Annotation(request.form, linkclick=True)
    with jsonlines.open(users[username]["logfile"], "a") as writer:
        writer.write(anot.to_json_dict())

    # retrieve the link target
    target = request.form["final_url"]
    return redirect(target)


@app.route("/annotate", methods=["POST"])
@logged_in
def annotate():
    username = request.cookies.get("username")
    anot = Annotation(request.form)
    with jsonlines.open(users[username]["logfile"], "a") as writer:
        writer.write(anot.to_json_dict())
    return redirect(url_for("annotate_random"))


@app.route("/wiki/<string:wiki_title>")
@logged_in
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
            response = redirect(url_for("index"))
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
