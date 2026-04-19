```python
from dataclasses import dataclass
from typing import Any, Optional, Callable


@dataclass
class FetchConfig:
    """Configuration for fetch operations."""
    retries: int = 3
    timeout: int = 5


class FetchLogger:
    """Handles logging for fetch operations."""
    
    def __init__(self):
        self.logs: list[str] = []
    
    def append(self, event: str) -> None:
        """Log an event."""
        self.logs.append(event)
    
    def clear(self) -> None:
        """Clear all logs."""
        self.logs.clear()


class CachedFetcher:
    """Manages HTTP fetching with caching, retries, and logging."""
    
    def __init__(self, config: Optional[FetchConfig] = None, logger: Optional[FetchLogger] = None):
        self.config = config or FetchConfig()
        self.logger = logger or FetchLogger()
        self.cache: dict[str, Any] = {}
    
    def fetch(self, url: str) -> Optional[str]:
        """
        Fetch data from a URL with caching and retry logic.
        
        Returns cached data if available, otherwise attempts to fetch with retries.
        Returns None if all retries are exhausted.
        """
        if url in self.cache:
            self.logger.append(f"hit {url}")
            return self.cache[url]
        
        self.logger.append(f"miss {url}")
        
        for attempt in range(self.config.retries):
            try:
                data = self._fetch_data(url)
                self.cache[url] = data
                self.logger.append(f"ok {url}")
                return data
            except Exception as e:
                self.logger.append(f"retry {url}")
        
        self.logger.append(f"fail {url}")
        return None
    
    def _fetch_data(self, url: str) -> str:
        """
        Simulate fetching data from a URL.
        In a real implementation, this would make an HTTP request.
        """
        return f"DATA:{url}"
    
    def clear_cache(self) -> None:
        """Clear the cache and log the event."""
        self.cache.clear()
        self.logger.append("cache cleared")
    
    def set_retries(self, n: int) -> None:
        """Update the number of retries."""
        self.config.retries = n
        self.logger.append(f"retries={n}")
```

## Refactoring Notes

**Key improvements:**

1. **Dependency Injection**: Replaced global state with object-oriented design. Config and logger are passed in, making the code testable and reusable.

2. **Type Hints**: Added modern Python type annotations for clarity and IDE support.

3. **Dataclass**: Used `@dataclass` for cleaner FetchConfig instead of a plain dict.

4. **Class-Based Logger**: Extracted logging into a dedicated `FetchLogger` class for separation of concerns.

5. **String Formatting**: Replaced string concatenation with f-strings for readability.

6. **Docstrings**: Added clear documentation for public methods.

7. **Explicit Extraction**: Moved the fake HTTP call into a separate `_fetch_data()` method, making it easier to replace with a real implementation.

8. **Better Exception Handling**: Captured the exception variable (though not used here, it's better practice than bare except).

9. **Loop Clarity**: Used `for attempt in range()` instead of while loop for clearer intent.

10. **Encapsulation**: All state is now managed within the `CachedFetcher` instance rather than scattered globals.

The refactored code maintains the same behavior while being more maintainable, testable, and following Python best practices.
