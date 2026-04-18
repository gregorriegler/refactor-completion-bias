```python
from enum import Enum, auto


class DocumentState(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


class Document:
    def __init__(self, text):
        self.text = text
        self._state = DocumentState.DRAFT

    @property
    def state(self):
        return self._state

    def status(self):
        return self._state.name.lower()

    def submit_for_review(self):
        if self._state is not DocumentState.DRAFT:
            raise RuntimeError("cannot submit")
        self._state = DocumentState.SUBMITTED

    def review(self, approved):
        if self._state is not DocumentState.SUBMITTED:
            raise RuntimeError("cannot review")
        self._state = DocumentState.APPROVED if approved else DocumentState.REVIEWED

    def publish(self):
        if self._state is not DocumentState.APPROVED:
            raise RuntimeError("cannot publish")
        self._state = DocumentState.PUBLISHED

    def archive(self):
        if self._state is DocumentState.ARCHIVED:
            raise RuntimeError("already archived")
        self._state = DocumentState.ARCHIVED
```
