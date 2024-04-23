#!/usr/bin/env python3

import hashlib
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

# basic passwd dict with sha256 hashed passwords
passwd = {"admin": hashlib.sha256("ahoj123".encode()).hexdigest(),
          "user": hashlib.sha256("helohelo".encode()).hexdigest()}

# example data: URL, Question, Answer (the Q and A are empty by default)
data = [
    ("https://en.wikipedia.org/wiki/Germany", "What is the capital of Germany?", "Berlin"),
    ("https://en.wikipedia.org/wiki/United_States", "What is the capital of the United States?", "Washington, D.C."),
    ("https://en.wikipedia.org/wiki/Canada", "What is the capital of Canada?", "Ottawa"),
    ("https://en.wikipedia.org/wiki/Czech_Republic", "What is the capital of the Czech Republic?", "Prague")]


@app.route("/")
def index():
    # check if logged in
    username = request.cookies.get("username")
    if username is not None:
        return redirect(url_for("annotate", url_id=0))
    else:
        # redirect to login page
        return redirect(url_for("login"))

@app.route("/annotate/<int:url_id>")
def annotate(url_id):
    # check if logged in
    username = request.cookies.get("username")

    if username is None:
        return redirect(url_for("login"))

    data_item = data[url_id]
    return render_template("annotate.html",
                           username=username,
                           url=data_item[0],
                           question=data_item[1],
                           answer=data_item[2])


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in passwd and passwd[username] == hashlib.sha256(password.encode()).hexdigest():
            response = redirect(url_for("annotate", url_id=0))
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
