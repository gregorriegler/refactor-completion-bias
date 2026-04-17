```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FetcherConfig:
    retries: int = 3
    timeout: int = 5


class Fetcher:
    def __init__(self, config: Optional[FetcherConfig] = None) -> None:
        self._config = config or FetcherConfig()
        self._cache: dict[str, str] = {}
        self._log: list[str] = []

    @property
    def log(self) -> list[str]:
        return self._log

    @property
    def config(self) -> FetcherConfig:
        return self._config

    def fetch(self, url: str) -> Optional[str]:
        if url in self._cache:
            self._log.append("hit " + url)
            return self._cache[url]

        self._log.append("miss " + url)

        for attempt in range(self._config.retries):
            try:
                data = "DATA:" + url
                self._cache[url] = data
                self._log.append("ok " + url)
                return data
            except Exception:
                self._log.append("retry " + url)

        self._log.append("fail " + url)
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        self._log.append("cache cleared")

    def set_retries(self, n: int) -> None:
        self._config.retries = n
        self._log.append("retries=" + str(n))
```
