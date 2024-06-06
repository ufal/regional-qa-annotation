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
users = {}

def get_user_annotations(username):
    annotations = {}
    with jsonlines.open(users[username]["logfile"]) as reader:
        for obj in reader:
            a = Annotation(obj)
            if a.wiki_title in annotations and a.time_saved > annotations[a.wiki_title].time_saved:
                annotations[a.wiki_title] = Annotation(obj)
            else:
                annotations[a.wiki_title] = Annotation(obj)

    return annotations

@app.template_filter()
def format_datetime(timestamp):
    return time.strftime("x%d. x%m. %Y, %H:%M:%S", time.localtime(timestamp)).replace("x0", "x").replace("x", "")

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
    username = request.cookies.get("username")
    annotations = get_user_annotations(username)
    numvalid = len([a for a in annotations.values() if not a.skipped])

    return render_template("dashboard.html",
                           username=username,
                           annotations=list(sorted(annotations.values(), key=lambda x: x.time_saved, reverse=True)),
                           numvalid=numvalid)


@app.route("/annotate/<string:wiki_title>")
@logged_in
def annotate_wiki(wiki_title):
    username = request.cookies.get("username")
    annotations = get_user_annotations(username)
    existing_annotation = annotations.get(
        wiki_title,
        Annotation.empty_annotation(wiki_title, users[username]["lang"], False))
    existing_annotation.time_loaded = time.time()

    return render_template(
        "annotate.html",
        username=username,
        editing=wiki_title in annotations and not annotations[wiki_title].skipped,
        data=existing_annotation)

@app.route("/annotate", methods=["GET"])
@logged_in
def annotate_random():
    username = request.cookies.get("username")
    random_title = get_random_article(users[username]["lang"])
    annotations = get_user_annotations(username)
    existing_annotation = annotations.get(
        random_title,
        Annotation.empty_annotation(random_title, users[username]["lang"], True))
    existing_annotation.time_loaded = time.time()

    return render_template(
        "annotate.html",
        username=username,
        editing=random_title in annotations and not annotations[random_title].skipped,
        data=existing_annotation)

@app.route("/linkclick", methods=["POST"])
@logged_in
def linkclick():
    username = request.cookies.get("username")
    anot = Annotation.from_request_form(request.form, linkclick=True)
    with jsonlines.open(users[username]["logfile"], "a") as writer:
        writer.write(anot.to_json_dict())

    # retrieve the link target
    target = request.form["final_url"]
    return redirect(target)


@app.route("/annotate", methods=["POST"])
@logged_in
def annotate():
    username = request.cookies.get("username")
    anot = Annotation.from_request_form(request.form)
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
                "login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    response = redirect(url_for("login"))
    response.set_cookie("username", "", expires=0)
    return response


if __name__ == "__main__":
    users = load_user_config("config/users.tsv")
    app.run(host="0.0.0.0", debug=True, port=8080)
