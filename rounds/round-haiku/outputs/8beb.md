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
    
    def __str__(self):
        return self.status.value
```

**Notes:** Replaced five boolean flags with a single enum-based state machine. This eliminates impossible states (like being both drafted and approved), reduces cognitive load, and simplifies state transitions and validation logic. The `status()` method is now implicit via `__str__()` or direct access to the status enum.
