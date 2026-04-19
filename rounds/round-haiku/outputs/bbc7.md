```python
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    retries: int = 3
    timeout: int = 5

class CachedFetcher:
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.cache: dict[str, str] = {}
        self.log: list[str] = []
    
    def fetch(self, url: str) -> Optional[str]:
        if url in self.cache:
            self._log(f"hit {url}")
            return self.cache[url]
        
        self._log(f"miss {url}")
        for attempt in range(self.config.retries):
            try:
                # pretend this is a real HTTP call
                data = f"DATA:{url}"
                self.cache[url] = data
                self._log(f"ok {url}")
                return data
            except Exception as e:
                self._log(f"retry {url}: {e}")
        
        self._log(f"fail {url}")
        return None
    
    def clear_cache(self) -> None:
        self.cache.clear()
        self._log("cache cleared")
    
    def set_retries(self, n: int) -> None:
        self.config.retries = n
        self._log(f"retries={n}")
    
    def _log(self, message: str) -> None:
        self.log.append(message)
        logger.info(message)
```

Refactoring notes:
- Encapsulated global state into a class to enable testing and multiple instances
- Replaced string concatenation with f-strings for clarity
- Added type hints for better code documentation
- Used dataclass for configuration
- Replaced unbounded while loop with explicit range iteration
- Added proper logging integration (while keeping the log list for backward compatibility)
- Improved exception handling to capture the actual exception (though the try/except is still somewhat vestigial since no real exception occurs)
