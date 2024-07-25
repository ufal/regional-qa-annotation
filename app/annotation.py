import time


class Annotation:

  wiki_lang: str
  wiki_title: str

  question: str
  question_en: str
  answer: str
  answer_en: str

  img_skipped: bool
  img_url: str
  img_question: str
  img_question_en: str
  img_answer: str
  img_answer_en: str

  time_loaded: float
  time_saved: float

  skipped: bool
  skipped_reason: str
  random_page: bool

  @staticmethod
  def empty_annotation(wiki_title: str, wiki_lang: str, random: bool):
    return Annotation({
      "wiki_lang": wiki_lang,
      "wiki_title": wiki_title,
      "skipped": False,
      "question": "",
      "question_en": "",
      "answer": "",
      "answer_en": "",
      "img_skipped": False,
      "img_url": "",
      "img_question": "",
      "img_question_en": "",
      "img_answer": "",
      "img_answer_en": "",
      "skipped_reason": "",
      "time_loaded": time.time(),
      "time_saved": time.time(),
      "random_page": random
    })

  @staticmethod
  def from_request_form(rf: dict):
    d = {}

    d["wiki_lang"] = rf["wiki_lang"]
    d["wiki_title"] = rf["wiki_title"]
    d["random_page"] = rf["randomness"] == "True"
    d["time_saved"] = time.time()
    d["time_loaded"] = float(rf["timestamp"])

    d["skipped"] = "skip" in rf or "linkskip" in rf

    if d["skipped"]:
      d["skipped_reason"] = "linkclick" if rf["clicked_url"] else "skip"
    else:
      d["question"] = rf["question"]
      d["question_en"] = rf["question_en"]
      d["answer"] = rf["answer"]
      d["answer_en"] = rf["answer_en"]

      d["img_skipped"] = "disable_img" in rf

      if not d["img_skipped"]:
        d["img_url"] = rf["img_url"]
        d["img_question"] = rf["img_question"]
        d["img_question_en"] = rf["img_question_en"]
        d["img_answer"] = rf["img_answer"]
        d["img_answer_en"] = rf["img_answer_en"]

    return Annotation(d)

  def __init__(self, d: dict):
    self.wiki_lang = d["wiki_lang"]
    self.wiki_title = d["wiki_title"]
    self.skipped = d["skipped"]
    self.time_loaded = float(d["time_loaded"])
    self.time_saved = float(d["time_saved"])
    self.random_page = d["random_page"]

    if not self.skipped:
      self.question = d["question"]
      self.question_en = d["question_en"]
      self.answer = d["answer"]
      self.answer_en = d["answer_en"]

      self.img_skipped = d["img_skipped"]
      if not self.img_skipped:
        self.img_url = d["img_url"]
        self.img_question = d["img_question"]
        self.img_question_en = d["img_question_en"]
        self.img_answer = d["img_answer"]
        self.img_answer_en = d["img_answer_en"]
    else:
      self.skipped_reason = d["skipped_reason"]

  @property
  def time_elapsed_seconds(self) -> int:
    return int(self.time_saved - self.time_loaded)

  def to_json_dict(self) -> dict:
    d = {
      "wiki_lang": self.wiki_lang,
      "wiki_title": self.wiki_title,
      "skipped": self.skipped,
      "time_loaded": self.time_loaded,
      "time_saved": self.time_saved,
      "random_page": self.random_page
    }

    if not self.skipped:
      d["question"] = self.question
      d["question_en"] = self.question_en
      d["answer"] = self.answer
      d["answer_en"] = self.answer_en

      d["img_skipped"] = self.img_skipped
      if not self.img_skipped:
        d["img_url"] = self.img_url
        d["img_question"] = self.img_question
        d["img_question_en"] = self.img_question_en
        d["img_answer"] = self.img_answer
        d["img_answer_en"] = self.img_answer_en

    else:
      d["skipped_reason"] = self.skipped_reason

    return d
