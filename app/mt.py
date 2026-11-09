"""Machine translation of a question/answer pair via an OpenAI-compatible LLM API.

The API key is read once, by load_key() at startup: from the systemd
credential `mt-llm-key` ($CREDENTIALS_DIRECTORY/mt-llm-key, see LoadCredential=
in the service unit), or else from the env variable MT_LLM_KEY.

Everything else is configured from the environment:

    MT_LLM_BASE    base URL of the OpenAI-compatible API (default
                   https://ai.ufal.mff.cuni.cz/api -- Open WebUI serves the
                   OpenAI-compatible API under /api, not /v1). A bare host gets
                   /v1/chat/completions appended; a base already ending in /v1
                   or /api is used as given.
    MT_LLM_KEY     bearer token, fallback for the mt-llm-key credential.
    MT_LLM_MODEL   model id as /models reports it, which need not match the
                   name shown in a web UI.
    MT_LLM_MAXTOK  completion budget (default 2048). Generous because gpt-oss
                   is a reasoning model: its thinking tokens are billed against
                   the same budget, and if they exhaust it the reply is cut off
                   before the JSON object is closed.
    MT_LLM_EFFORT  reasoning effort, "low" by default because thinking tokens
                   dominate the wall clock on a task this short. Set it to
                   "medium"/"high" for more deliberation, or to the empty string
                   to leave the server default alone.
    MT_LLM_TIMEOUT seconds to wait for one completion (default 120).

`python3 -m app.mt` checks the credentials and lists the model ids.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request


DEFAULT_BASE = "https://ai.ufal.mff.cuni.cz/api"
CREDENTIAL_NAME = "mt-llm-key"

_api_key = ""


def _base():
    return os.environ.get("MT_LLM_BASE", DEFAULT_BASE).rstrip("/")


def load_key():
    """Read the API key: the systemd credential, else the env variable.

    Raises RuntimeError when neither is set.
    """
    global _api_key
    cred_dir = os.environ.get("CREDENTIALS_DIRECTORY")
    if cred_dir:
        try:
            with open(os.path.join(cred_dir, CREDENTIAL_NAME), encoding="utf8") as f:
                _api_key = f.read().strip()
        except OSError:
            pass
    if not _api_key:
        _api_key = os.environ.get("MT_LLM_KEY", "").strip()
    if not _api_key:
        raise RuntimeError(
            f"MT is enabled but there is no API key: neither the "
            f"{CREDENTIAL_NAME} credential nor MT_LLM_KEY is set")
    return _api_key


def _key():
    return _api_key


def _model():
    return os.environ.get("MT_LLM_MODEL", "gpt-oss-120b")


def _maxtok():
    return int(os.environ.get("MT_LLM_MAXTOK", "2048"))


def _timeout():
    return float(os.environ.get("MT_LLM_TIMEOUT", "120"))


def _effort():
    """Reasoning effort to ask for; "" leaves the server default alone.

    "low" by default: thinking tokens are most of the latency. A server that
    rejects the parameter is retried without it, see chat().
    """
    return os.environ.get("MT_LLM_EFFORT", "low").strip()


def endpoint():
    """Chat-completions URL. Accepts a base with or without a /v1 or /api suffix."""
    base = _base()
    if base.endswith(("/v1", "/api")):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def models():
    """List the models the service exposes -- used to check credentials."""
    url = endpoint().rsplit("/chat/completions", 1)[0] + "/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_key()}"})
    with urllib.request.urlopen(req, timeout=_timeout()) as r:
        return json.load(r)


PARAM_REJECTED = re.compile(
    r"reasoning[_ ]effort|unknown|unrecognized|unexpected|extra field",
    re.IGNORECASE)


def chat(messages, temperature=0.0, max_tokens=None, retries=2, stats=None):
    """One chat completion, retried on transient failure. Returns the text.

    If `stats` is a dict it is filled in with what the round trip cost, so the
    caller can log where the time went: `api_seconds` (summed over attempts),
    `attempts`, `finish_reason`, `effort`, and the token counts the server
    reported, including `reasoning_tokens` where it reports them.

    Raises RuntimeError with a message meant to be shown to the annotator.
    """
    headers = {"Authorization": f"Bearer {_key()}",
               "Content-Type": "application/json"}
    effort = _effort()
    stats = stats if stats is not None else {}
    stats.setdefault("api_seconds", 0.0)
    stats.setdefault("attempts", 0)
    last = None

    for attempt in range(retries):
        payload = {
            "model": _model(),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or _maxtok(),
        }
        if effort:
            payload["reasoning_effort"] = effort
        stats["effort"] = effort or "server default"
        stats["attempts"] = attempt + 1

        started = time.time()
        try:
            req = urllib.request.Request(
                endpoint(), data=json.dumps(payload).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=_timeout()) as r:
                response = json.load(r)
            stats["api_seconds"] += time.time() - started

            ch = response["choices"][0]
            stats["finish_reason"] = ch.get("finish_reason")
            usage = response.get("usage") or {}
            stats["prompt_tokens"] = usage.get("prompt_tokens")
            stats["completion_tokens"] = usage.get("completion_tokens")
            stats["reasoning_tokens"] = (
                usage.get("completion_tokens_details") or {}).get(
                    "reasoning_tokens")

            text = (ch.get("message") or {}).get("content") or ""
            if not text.strip():
                # A reasoning model that spent the whole budget thinking. Asking
                # again the same way would just burn another timeout, so drop to
                # the cheapest effort for the retry.
                effort = "low"
                raise RuntimeError(
                    f"the model returned no text (finish_reason="
                    f"{ch.get('finish_reason')}, "
                    f"{usage.get('completion_tokens')} completion tokens); "
                    f"raise MT_LLM_MAXTOK or lower MT_LLM_EFFORT")
            return text
        except RuntimeError as e:                 # empty/truncated completion
            last = str(e)
        except urllib.error.HTTPError as e:
            stats["api_seconds"] += time.time() - started
            detail = e.read()[:400].decode("utf8", "replace")
            last = f"HTTP {e.code}: {detail}"
            # A server that does not support reasoning_effort rejects the whole
            # request; drop the parameter and let the retry run without it.
            if e.code in (400, 422) and effort and PARAM_REJECTED.search(detail):
                stats["effort_rejected"] = True
                effort = ""
                continue
            if e.code in (400, 401, 403, 404):    # not transient, do not hammer
                raise RuntimeError(last) from None
        except Exception as e:                    # noqa: BLE001 - network flake
            stats["api_seconds"] += time.time() - started
            last = f"{type(e).__name__}: {e}"
    raise RuntimeError(last or "no response from the translation service")


def _extract_json_object(text):
    """Pull the first balanced {...} out of a completion.

    A reasoning model likes to wrap its answer in prose or a ``` fence even when
    told not to, so parsing the whole completion as JSON is not enough.
    """
    text = re.sub(r"^\s*```(?:json)?|```\s*$", "", text.strip())
    start = text.find("{")
    if start < 0:
        raise RuntimeError("the model did not return a JSON object")

    depth, in_str, esc = 0, False, False
    for i, c in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"unparseable JSON from the model: {e}") from None
    raise RuntimeError("the reply was cut off before the JSON was complete")


SYSTEM_PROMPT = (
    "You are a professional translator preparing a multilingual "
    "question-answering dataset. You translate faithfully and literally, you "
    "never answer or comment on the questions you translate, and you reply "
    "with nothing but the requested JSON object."
)


def build_prompt(lang_name, country, wiki_title, question, answer, visual=False):
    """The user message asking for both halves of one Q&A pair at once.

    Both are translated in a single request on purpose: the answer is often a
    bare name or number whose grammatical form and reading only make sense
    together with the question.
    """
    about = f"about {country}" if country else "about a specific country or region"
    lines = [
        f"Translate the following question and its answer from {lang_name} "
        f"into English.",
        "",
        f"Context: this is a deliberately region-specific trivia question "
        f"{about}, written by a local annotator from the Wikipedia article "
        f"titled \"{wiki_title}\". Local knowledge is the whole point of the "
        f"question, so people, places, institutions, works, events and "
        f"products in it are usually specific to that country and may have no "
        f"English equivalent.",
        "",
        "Rules:",
        "- Translate the question and the answer as one unit: the answer "
        "answers the question, so use each as context for the other and keep "
        "them consistent.",
        "- Translate only. Do not answer the question yourself, do not add "
        "explanations, background, glosses or notes, and do not expand "
        "abbreviations that the source leaves short.",
        "- Prefer local-language names and spellings over English ones, unless the English "
        "name is widely used in English (e.g. \"Prague\" not \"Praha\").",
        "- Keep the answer as close to the the original as possible: if it is a bare name, "
        "number or date, the translation is too.",
        "- Keep units, numbers and dates as they are.",
    ]
    if visual:
        lines.append(
            "- The pair refers to a photograph in the article, so keep the "
            "deictic wording (\"in the picture\", \"shown here\").")
    lines += [
        "",
        'Reply with exactly this JSON object and nothing else: '
        '{"question_en": "...", "answer_en": "..."}',
        "",
        f"Question ({lang_name}): {question}",
        f"Answer ({lang_name}): {answer}",
    ]
    return "\n".join(lines)


def translate_qa(question, answer, lang_name, country="", wiki_title="",
                 visual=False, stats=None):
    """Translate one question/answer pair into English.

    Returns {"question_en": str, "answer_en": str}; raises RuntimeError with a
    message suitable for showing to the annotator.
    """
    text = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(
            lang_name, country, wiki_title, question, answer, visual)},
    ], stats=stats)
    data = _extract_json_object(text)

    out = {}
    for field in ("question_en", "answer_en"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"the model did not return {field}")
        out[field] = value.strip()
    return out


if __name__ == "__main__":
    # credential check: list the models the key can reach
    try:
        load_key()
    except RuntimeError as e:
        sys.exit(str(e))
    print(f"base     {_base()}")
    print(f"endpoint {endpoint()}")
    print(f"key      set, {len(_key())} chars")
    print(f"model    {_model()}")
    print(f"maxtok   {_maxtok()}")
    try:
        data = models()
    except Exception as e:                        # noqa: BLE001
        sys.exit(f"\n/models failed: {type(e).__name__}: {e}\n"
                 f"try MT_LLM_BASE with or without a /v1 suffix")
    ids = [m.get("id", "?") for m in
           data.get("data", data if isinstance(data, list) else [])]
    print(f"\n{len(ids)} models reachable:")
    for i in sorted(ids):
        print(f"  {i}")
    print(f"\nMT_LLM_MODEL={_model()} {'is' if _model() in ids else 'is NOT'} "
          f"in the list")
