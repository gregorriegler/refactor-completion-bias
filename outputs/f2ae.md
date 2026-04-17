```python
from enum import Enum, auto


class DocumentState(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


_VALID_TRANSITIONS = {
    DocumentState.DRAFT: {DocumentState.SUBMITTED},
    DocumentState.SUBMITTED: {DocumentState.REVIEWED},
    DocumentState.REVIEWED: {DocumentState.APPROVED, DocumentState.SUBMITTED},
    DocumentState.APPROVED: {DocumentState.PUBLISHED},
    DocumentState.PUBLISHED: {DocumentState.ARCHIVED},
    DocumentState.ARCHIVED: set(),
}


class Document:
    def __init__(self, text: str) -> None:
        self.text = text
        self._state = DocumentState.DRAFT

    @property
    def state(self) -> DocumentState:
        return self._state

    def _transition(self, target: DocumentState) -> None:
        allowed = _VALID_TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise RuntimeError(
                f"cannot transition from {self._state.name} to {target.name}"
            )
        self._state = target

    def submit_for_review(self) -> None:
        self._transition(DocumentState.SUBMITTED)

    def review(self, approved: bool) -> None:
        if self._state is not DocumentState.SUBMITTED:
            raise RuntimeError(
                f"cannot review a document in state {self._state.name}"
            )
        self._state = DocumentState.APPROVED if approved else DocumentState.REVIEWED

    def publish(self) -> None:
        self._transition(DocumentState.PUBLISHED)

    def archive(self) -> None:
        if self._state is DocumentState.ARCHIVED:
            raise RuntimeError("already archived")
        self._state = DocumentState.ARCHIVED

    def status(self) -> str:
        return self._state.name.lower()
```
