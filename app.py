#!/usr/bin/env python3
import hashlib
import jsonlines
import requests
import time
from flask import Flask, render_template, request, redirect, url_for
from functools import wraps
from langcodes import Language

from app.annotation import Annotation
from app.user import User, load_users_from_json

app = Flask(__name__)
users = {}

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
    else:
        return ""

@app.template_filter()
def format_datetime(timestamp):
    print("timestamp is",timestamp)
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
    user = users[request.cookies.get("username")]
    annotations = dict(sorted(user.load_annotations().items(), key=lambda x: x[1].time_saved, reverse=True))
    return render_template("dashboard.html", user=user, annotations=annotations)
                           
                           


@app.route("/annotate/<string:wiki_title>")
@logged_in
def annotate_wiki(wiki_title):
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

@app.route("/linkclick", methods=["POST"])
@logged_in
def linkclick():
    user = users[request.cookies.get("username")]
    anot = Annotation.from_request_form(request.form, linkclick=True)
    with jsonlines.open(user.data_file, "a") as writer:
        writer.write(anot.to_json_dict())

    # retrieve the link target
    target = request.form["final_url"]
    return redirect(target)


@app.route("/annotate", methods=["POST"])
@logged_in
def annotate():
    user = users[request.cookies.get("username")]
    anot = Annotation.from_request_form(request.form)
    with jsonlines.open(user.data_file, "a") as writer:
        writer.write(anot.to_json_dict())
    return redirect(url_for("annotate_random"))


@app.route("/wiki/<string:wiki_title>")
@logged_in
def wiki(wiki_title):
    # we are including texts from wiki - we can intercept this route to switch
    # articles
    return redirect(url_for("annotate_wiki", wiki_title=wiki_title))

@app.route("/admin")
@logged_in
def admin():
    user = users[request.cookies.get("username")]
    if user.role == "admin":
        return render_template("admin.html", user=user, users=users)
    else:
        return redirect(url_for("index"))
    

@app.route("/login", methods=["POST", "GET"])
def login():
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
    users = load_users_from_json("config/users.json")
    app.run(host="0.0.0.0", debug=True, port=8080)
