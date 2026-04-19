```python
from enum import Enum


class DocumentStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Document:
    def __init__(self, text):
        self.text = text
        self.status = DocumentStatus.DRAFT

    def submit_for_review(self):
        if self.status != DocumentStatus.DRAFT:
            raise RuntimeError("cannot submit")
        self.status = DocumentStatus.SUBMITTED

    def review(self, approved):
        if self.status != DocumentStatus.SUBMITTED:
            raise RuntimeError("cannot review")
        self.status = DocumentStatus.APPROVED if approved else DocumentStatus.REVIEWED

    def publish(self):
        if self.status not in (DocumentStatus.APPROVED, DocumentStatus.REVIEWED):
            raise RuntimeError("cannot publish")
        self.status = DocumentStatus.PUBLISHED

    def archive(self):
        if self.status == DocumentStatus.ARCHIVED:
            raise RuntimeError("already archived")
        self.status = DocumentStatus.ARCHIVED
```

Key improvements:
- Replaced 5 boolean flags with a single `DocumentStatus` enum that makes the workflow explicit and impossible to reach invalid states
- Each state is now atomic and mutually exclusive
- Validation logic is clearer: checking a single enum value instead of multiple boolean conditions
- The status() method is eliminated entirely since we now have a direct status field
- State transitions are explicit and the valid paths through the workflow are evident from the code
- Archived state is still a terminal state (any non-archived state can transition to it)
