```python
from typing import Any, Optional
from dataclasses import dataclass
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FetchConfig:
    """Configuration for fetch behavior."""
    retries: int = 3
    timeout: int = 5


class CachingFetcher:
    """Manages HTTP fetch operations with caching and retry logic."""
    
    def __init__(self, config: Optional[FetchConfig] = None):
        self.config = config or FetchConfig()
        self.cache: dict[str, str] = {}
    
    def fetch(self, url: str) -> Optional[str]:
        """
        Fetch data from URL with caching and retry logic.
        
        Args:
            url: The URL to fetch from
            
        Returns:
            The fetched data, or None if all retries failed
        """
        if url in self.cache:
            logger.info(f"Cache hit for {url}")
            return self.cache[url]
        
        logger.info(f"Cache miss for {url}")
        
        for attempt in range(self.config.retries):
            try:
                # Placeholder for real HTTP call
                data = f"DATA:{url}"
                self.cache[url] = data
                logger.info(f"Successfully fetched {url}")
                return data
            except Exception as e:
                logger.warning(f"Retry {attempt + 1} for {url}: {e}")
        
        logger.error(f"Failed to fetch {url} after {self.config.retries} retries")
        return None
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def set_retries(self, n: int) -> None:
        """Set the number of retries."""
        self.config.retries = n
        logger.info(f"Retries set to {n}")


# Legacy module-level interface for backward compatibility
_default_fetcher = CachingFetcher()

def fetch(url: str) -> Optional[str]:
    """Module-level fetch function using default fetcher."""
    return _default_fetcher.fetch(url)

def clear_cache() -> None:
    """Module-level cache clear using default fetcher."""
    _default_fetcher.clear_cache()

def set_retries(n: int) -> None:
    """Module-level retry configuration using default fetcher."""
    _default_fetcher.set_retries(n)
```

## Refactoring Notes

**Key improvements:**
1. **Encapsulation** - Wrapped global state into a `CachingFetcher` class, allowing multiple independent instances and testability
2. **Logging** - Replaced manual LOG list with proper Python logging module
3. **Type hints** - Added full type annotations for better IDE support and clarity
4. **Documentation** - Added docstrings for the class and methods
5. **Configuration** - Used dataclass for typed configuration with defaults
6. **String formatting** - Replaced concatenation with f-strings
7. **Exception handling** - More specific error messages (though still catching broad Exception since the actual HTTP call is mocked)
8. **Backward compatibility** - Kept module-level functions for existing callers

The refactored code separates concerns (caching, retry logic, logging) into a cohesive class while maintaining the original API through wrapper functions. This makes it much easier to test, extend, and integrate with other systems.
