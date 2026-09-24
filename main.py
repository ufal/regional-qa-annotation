#!/usr/bin/env python3
import hashlib
import jsonlines
import random
import requests
import time
from flask import Flask, render_template, request, redirect, url_for
from functools import wraps
from langcodes import Language

from app.annotation import Annotation
from app.user import User, load_users_from_json
from app.config import load_wiki_titles_from_urls, load_wiki_titles

USERS_FILE = "config/users.json"

WIKI_LANGS = ["cs", "sk", "uk", "no", "nn"]
WIKI_LISTS_SPARQL = {lang: f"data/{lang}_wiki_fixed.txt" for lang in WIKI_LANGS}
WIKI_LISTS_LOCAL = {lang: f"data/{lang}_articles_only.txt" for lang in WIKI_LANGS}

app = Flask(__name__)

@app.template_filter()
def valid(annotations):
    return {k: v for k, v in annotations.items() if not v.skipped}

@app.template_filter()
def skipped(annotations):
    return {k: v for k, v in annotations.items() if v.skipped}

@app.template_filter()
def median_time_spent(annotations):
    times = [a.time_saved - a.time_loaded for a in annotations.values()]
    if not times:
        return 0

    times.sort()
    n = len(times)
    if n % 2 == 0:
        return (times[n // 2 - 1] + times[n // 2]) / 2
    else:
        return times[n // 2]

@app.template_filter()
def time_spent(annotations):
    return sum(a.time_saved - a.time_loaded for a in annotations.values())

@app.template_filter()
def lang_name(lang):
    return Language.get(lang).display_name()

@app.template_filter()
def lang_flag(lang):
    # support czech, slovak, ukrainian, romanian, italian, english and german, return utf-8 flag emojis
    lang = lang.lower()
    if lang == "cs":
        return "🇨🇿"
    elif lang == "sk":
        return "🇸🇰"
    elif lang == "uk":
        return "🇺🇦"
    elif lang == "ro":
        return "🇷🇴"
    elif lang == "it":
        return "🇮🇹"
    elif lang == "en":
        return "🇬🇧"
    elif lang == "de":
        return "🇩🇪"
    elif lang in ("no", "nn"):
        return "🇳🇴"
    else:
        return ""

@app.template_filter()
def format_datetime(timestamp):
    return time.strftime("x%d. x%m. %Y, %H:%M:%S", time.localtime(timestamp)).replace("x0", "x").replace("x", "")

def get_random_article(lng):
    article_pool = []
    if lng in WIKI_LISTS_SPARQL:
        article_pool.extend(load_wiki_titles_from_urls(WIKI_LISTS_SPARQL[lng]))

    if lng in WIKI_LISTS_LOCAL:
        article_pool.extend(load_wiki_titles(WIKI_LISTS_LOCAL[lng]))

    if article_pool:
        return random.choice(article_pool)

    url = f"https://{lng}.wikipedia.org/api/rest_v1/page/random/summary"
    response = requests.get(url)
    return response.json().get("titles", {}).get("canonical")

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
    users = load_users_from_json(USERS_FILE)
    user = users[request.cookies.get("username")]
    annotations = dict(sorted(user.load_annotations().items(), key=lambda x: x[1].time_saved, reverse=True))
    return render_template("dashboard.html", user=user, annotations=annotations)


@app.route("/annotate/<string:wiki_title>")
@logged_in
def annotate_wiki(wiki_title):
    wiki_title = wiki_title.encode("latin-1").decode("utf-8")

    users = load_users_from_json(USERS_FILE)
    user = users[request.cookies.get("username")]
    annotations = user.load_annotations()
    existing_annotation = annotations.get(
        wiki_title,
        Annotation.empty_annotation(wiki_title, user.lang, False))
    existing_annotation.time_loaded = time.time()

    return render_template(
        "annotate.html",
        user=user,
        editing=wiki_title in annotations and not annotations[wiki_title].skipped,
        data=existing_annotation)

@app.route("/annotate", methods=["GET"])
@logged_in
def annotate_random():
    users = load_users_from_json(USERS_FILE)
    user = users[request.cookies.get("username")]
    random_title = get_random_article(user.lang)
    annotations = user.load_annotations()
    existing_annotation = annotations.get(
        random_title,
        Annotation.empty_annotation(random_title, user.lang, True))
    existing_annotation.time_loaded = time.time()

    return render_template(
        "annotate.html",
        user=user,
        editing=random_title in annotations and not annotations[random_title].skipped,
        data=existing_annotation)

@app.route("/annotate", methods=["POST"])
@logged_in
def annotate():
    users = load_users_from_json(USERS_FILE)
    user = users[request.cookies.get("username")]
    anot = Annotation.from_request_form(request.form)
    with jsonlines.open(user.data_file, "a") as writer:
        writer.write(anot.to_json_dict())

    if request.form["clicked_url"]:
        return redirect(request.form["clicked_url"])
    else:
        return redirect(url_for("annotate_random"))


@app.route("/wiki/<string:wiki_title>")
@logged_in
def wiki(wiki_title):
    # we are including texts from wiki - we can intercept this route to switch
    # articles
    wiki_title = wiki_title.encode("latin-1").decode("utf-8")
    return redirect(url_for("annotate_wiki", wiki_title=wiki_title))

@app.route("/admin")
@logged_in
def admin():
    users = load_users_from_json(USERS_FILE)
    user = users[request.cookies.get("username")]
    if user.role == "admin":
        return render_template("admin.html", user=user, users=users)
    else:
        return redirect(url_for("index"))

# admin/user should show the dashboard of that user
@app.route("/admin/user/<string:username>")
@logged_in
def admin_user(username):
    users = load_users_from_json(USERS_FILE)
    user = users[request.cookies.get("username")]
    if user.role == "admin":
        return render_template("dashboard.html", user=users[username], annotations=users[username].load_annotations())
    else:
        return redirect(url_for("index"))


@app.route("/login", methods=["POST", "GET"])
def login():
    users = load_users_from_json(USERS_FILE)
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(
            request.form["password"].encode()).hexdigest()

        if username in users and users[username].passwd == password:
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
    app.run(host="0.0.0.0", debug=True, port=8080)
