# Example 10: Global state and side effects

```python
CACHE = {}
LOG = []
CONFIG = {"retries": 3, "timeout": 5}

def fetch(url):
    if url in CACHE:
        LOG.append("hit " + url)
        return CACHE[url]
    LOG.append("miss " + url)
    attempts = 0
    while attempts < CONFIG["retries"]:
        try:
            # pretend this is a real HTTP call
            data = "DATA:" + url
            CACHE[url] = data
            LOG.append("ok " + url)
            return data
        except Exception:
            attempts += 1
            LOG.append("retry " + url)
    LOG.append("fail " + url)
    return None

def clear_cache():
    global CACHE
    CACHE = {}
    LOG.append("cache cleared")

def set_retries(n):
    CONFIG["retries"] = n
    LOG.append("retries=" + str(n))
```
