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

## Machine translation

Annotators in selected languages get a **Translate with MT** button that fills
in the English question and answer from the ones they wrote in their own
language. There is one button per pair (plain text and image); each sends the
question and the answer to the model in a *single* request, so the model has the
question as context for the answer, which is often just a bare name or number.
The prompt also tells the model that this is a deliberately region-specific
question about the annotator's country, and names the Wikipedia article it came
from. Both buttons stay disabled until the question and the answer are filled
in, and the status line next to a button reminds the annotator to check the
result.

Whether the English text came out of MT is recorded in the data: the keys
`mt_used` and `img_mt_used` are written to a record only when the annotator
used the button for that pair (possibly editing the output afterwards), so
older records and hand-translated ones are unchanged.

### Which languages

`MT_LANGS` in `main.py` lists the languages the button is offered in. It is
empty by default, so MT is off for every language until switched on. The
environment variable `MT_LANGS` (comma- or space-separated codes) overrides it
without a code change.

### The LLM service

`app/mt.py` talks to any OpenAI-compatible chat API — in our case the UFAL
gpt-oss instance.

The API key is passed to the service as the systemd credential `mt-llm-key`.
Keep the key in a file readable only by root and add to the `[Service]`
section of the unit:

```ini
LoadCredential=mt-llm-key:/etc/regional-qa/mt-llm-key
```

When `MT_LANGS` is not empty, the key is read once at startup from
`$CREDENTIALS_DIRECTORY/mt-llm-key`, or from the env variable `MT_LLM_KEY` if
the credential is not there. **If there is no key, the app refuses to start.**
`systemctl start` does not report that, so after changing the key or
`MT_LANGS` check the service:

```sh
systemctl restart regional-qa && systemctl status regional-qa
```

The rest is set with environment variables in the unit:

| variable | meaning |
| --- | --- |
| `MT_LLM_KEY` | bearer token, fallback for the `mt-llm-key` credential |
| `MT_LLM_BASE` | API base, default `https://ai.ufal.mff.cuni.cz/api` (Open WebUI serves the OpenAI-compatible API under `/api`, not `/v1`) |
| `MT_LLM_MODEL` | model id as `/models` reports it, default `gpt-oss-120b` |
| `MT_LLM_EFFORT` | reasoning effort, default `low`. **This is the main lever on how long a translation takes** — see below. Empty string leaves the server default |
| `MT_LLM_MAXTOK` | completion budget, default 2048. gpt-oss is a reasoning model and its thinking tokens come out of the same budget, so a small value truncates the reply |
| `MT_LLM_TIMEOUT` | seconds to wait for one completion, default 120 |

To check the key and see which model ids it can reach (outside the service,
the key comes from the env variable):

```sh
MT_LLM_KEY=... env/bin/python -m app.mt
```