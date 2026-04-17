```python
from enum import Enum, auto


class Status(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


class Document:
    def __init__(self, text):
        self.text = text
        self._status = Status.DRAFT

    def submit_for_review(self):
        if self._status != Status.DRAFT:
            raise RuntimeError("cannot submit")
        self._status = Status.SUBMITTED

    def review(self, approved):
        if self._status != Status.SUBMITTED:
            raise RuntimeError("cannot review")
        self._status = Status.APPROVED if approved else Status.REVIEWED

    def publish(self):
        if self._status != Status.APPROVED:
            raise RuntimeError("cannot publish")
        self._status = Status.PUBLISHED

    def archive(self):
        if self._status == Status.ARCHIVED:
            raise RuntimeError("already archived")
        self._status = Status.ARCHIVED

    def status(self):
        return self._status.name.lower()
```
