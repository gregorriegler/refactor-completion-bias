```python
from enum import Enum


class DocumentState(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Document:
    def __init__(self, text):
        self.text = text
        self.state = DocumentState.DRAFT
    
    def submit_for_review(self):
        if self.state != DocumentState.DRAFT:
            raise RuntimeError("cannot submit")
        self.state = DocumentState.SUBMITTED
    
    def review(self, approved):
        if self.state != DocumentState.SUBMITTED:
            raise RuntimeError("cannot review")
        self.state = DocumentState.REVIEWED
        if approved:
            self.state = DocumentState.APPROVED
    
    def publish(self):
        if self.state != DocumentState.APPROVED:
            raise RuntimeError("cannot publish")
        self.state = DocumentState.PUBLISHED
    
    def archive(self):
        if self.state == DocumentState.ARCHIVED:
            raise RuntimeError("already archived")
        self.state = DocumentState.ARCHIVED
    
    def status(self):
        return self.state.value
```

**Refactoring notes:**

- Replaced five boolean flags with a single `DocumentState` enum that captures the document's lifecycle explicitly.
- Each method now checks a single state condition instead of multiple boolean combinations, making the code more readable and maintainable.
- The state transitions are now linear and unambiguous: draft → submitted → reviewed → (approved or reviewed) → published → archived.
- The `status()` method is now trivial and complete—it returns the actual state rather than inferring it from multiple flags.
- The enum makes the valid states and transitions discoverable and type-safe.
