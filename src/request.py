import string
import random


class ClipRequest:
    def __init__(self, url, a, b, cat=None, name=None, _id=None):
        self.url = url
        self.interval = a, b
        self.cat = cat
        self.name = name
        self.id = _id or _gen_id()

    @classmethod
    def from_json(cls, obj):
        try:
            url = obj["url"]
            a, b = obj["start"], obj["end"]
            _id = obj["id"]
            cat = obj.get("category")
            name = obj.get("name")
            return cls(url, a, b, cat, name, _id)
        except Exception:
            print("Invalid json")

    @property
    def json(self):
        return dict(
            url=self.url,
            start=self.interval[0],
            end=self.interval[1],
            category=self.cat,
            name=self.name,
            id=self.id
        )

    @property
    def complete(self):
        return self.url and self.interval[0] and self.interval[1] and self.cat and self.name


def _gen_id():
    return "".join(random.choices(string.ascii_letters, k=4))
