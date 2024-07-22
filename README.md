# regional-qa-annotation
A web-based annotation tool for creating regional question-answer pairs


## Setup

The project files are located in `/var/www/regional-qa-annotation`.

### nginx

Listens on 8080, inserts "/regional-qa/" back in the request URL because the main quest machine strips it off.
Config file in `/etc/nginx/sites-available/regional-qa`.

### gunicorn

Runs as a service configured in `/etc/systemd/system/regional-qa.service`.
This sets cwd to the project path, sets `SCRIPT_NAME` env variable to `/regional-qa` (which tells the flask app to strip this prefix off before giving it to Python,
and to **insert** the prefix back again when creating links and such); then it runs the server with n (3) workers and communicates with nginx via a unix socket.

When run, gunicorn is provided with a python module and a flask app object. This is `app` in `wsgi.py`.