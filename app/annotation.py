import time


class Annotation:

  wiki_lang: str
  wiki_title: str

  question: str
  answer: str

  img_skipped: bool
  img_url: str
  img_question: str
  img_answer: str

  #time_loaded: float
  time_saved: float

  skipped: bool
  #random_page: bool

  def __init__(self, rf: dict):
    self.wiki_title = rf["wiki_title"]
    self.wiki_lang = rf["wiki_lang"]
    self.skipped = "skip" in rf
    self.time_saved = time.time()

    self.img_skipped = "disable_img" in rf

    if not self.skipped:
      self.question = rf["question"]
      self.answer = rf["answer"]

      if not self.img_skipped:
        self.img_url = rf["imgurl"]
        self.img_question = rf["img_question"]
        self.img_answer = rf["img_answer"]


  def to_json_dict(self) -> dict:
    d = {
      "wiki_lang": self.wiki_lang,
      "wiki_title": self.wiki_title,
      "skipped": self.skipped,
      #"time_loaded": self.time_loaded,
      "time_saved": self.time_saved,
      #"random_page": self.random_page
    }

    if not self.skipped:
      d["question"] = self.question
      d["answer"] = self.answer

      d["img_skipped"] = self.img_skipped
      if not self.img_skipped:
        d["img_url"] = self.img_url
        d["img_question"] = self.img_question
        d["img_answer"] = self.img_answer

    return d

