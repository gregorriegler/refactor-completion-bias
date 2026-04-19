# Example 14: Monolithic HTTP request handler

```python
import json
import hashlib
import time

SESSIONS = {}
USERS = {"admin": {"pw": "adminhash", "role": "admin"}}
POSTS = {}
COMMENTS = {}
RATE_LIMIT = {}

def handle_request(method, path, headers, body, db):
    now = time.time()
    ip = headers.get("x-forwarded-for", "unknown")
    bucket = RATE_LIMIT.setdefault(ip, [])
    bucket[:] = [t for t in bucket if now - t < 60]
    if len(bucket) >= 100:
        return 429, {"content-type": "application/json"}, json.dumps({"error": "rate limit"})
    bucket.append(now)
    auth = None
    if "authorization" in headers:
        token = headers["authorization"].replace("Bearer ", "")
        sess = SESSIONS.get(token)
        if sess and sess["expires"] > now:
            auth = sess["user"]
    try:
        parsed = json.loads(body) if body else {}
    except Exception:
        return 400, {"content-type": "application/json"}, json.dumps({"error": "bad json"})
    parts = [p for p in path.split("/") if p]
    if method == "POST" and parts == ["auth", "login"]:
        u = parsed.get("username")
        p = parsed.get("password")
        if not u or not p:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "missing"})
        user = USERS.get(u)
        h = hashlib.sha256(p.encode()).hexdigest()
        if not user or user["pw"] != h:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "bad creds"})
        token = hashlib.sha256((u + str(now)).encode()).hexdigest()
        SESSIONS[token] = {"user": u, "expires": now + 3600}
        return 200, {"content-type": "application/json"}, json.dumps({"token": token})
    if method == "POST" and parts == ["auth", "logout"]:
        if "authorization" in headers:
            tok = headers["authorization"].replace("Bearer ", "")
            SESSIONS.pop(tok, None)
        return 204, {}, ""
    if method == "POST" and parts == ["users"]:
        u = parsed.get("username")
        p = parsed.get("password")
        e = parsed.get("email")
        if not u or not p or not e:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "missing"})
        if len(p) < 8:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "pw short"})
        if "@" not in e:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad email"})
        if u in USERS:
            return 409, {"content-type": "application/json"}, json.dumps({"error": "exists"})
        USERS[u] = {"pw": hashlib.sha256(p.encode()).hexdigest(), "role": "user", "email": e}
        db.execute("INSERT INTO users(name,email) VALUES (?,?)", (u, e))
        return 201, {"content-type": "application/json"}, json.dumps({"username": u})
    if method == "GET" and len(parts) == 1 and parts[0] == "posts":
        limit = int(headers.get("x-limit", "20"))
        offset = int(headers.get("x-offset", "0"))
        items = list(POSTS.values())
        items.sort(key=lambda p: p["created"], reverse=True)
        page = items[offset:offset+limit]
        return 200, {"content-type": "application/json"}, json.dumps({"items": page, "total": len(items)})
    if method == "GET" and len(parts) == 2 and parts[0] == "posts":
        pid = parts[1]
        post = POSTS.get(pid)
        if not post:
            return 404, {"content-type": "application/json"}, json.dumps({"error": "not found"})
        cs = [c for c in COMMENTS.values() if c["post"] == pid]
        return 200, {"content-type": "application/json"}, json.dumps({"post": post, "comments": cs})
    if method == "POST" and parts == ["posts"]:
        if not auth:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "auth"})
        title = parsed.get("title")
        content = parsed.get("content")
        if not title or len(title) > 200:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad title"})
        if not content or len(content) > 10000:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad content"})
        pid = hashlib.sha256((auth + title + str(now)).encode()).hexdigest()[:12]
        POSTS[pid] = {"id": pid, "title": title, "content": content, "author": auth, "created": now}
        db.execute("INSERT INTO posts(id,author,title) VALUES (?,?,?)", (pid, auth, title))
        return 201, {"content-type": "application/json"}, json.dumps(POSTS[pid])
    if method == "DELETE" and len(parts) == 2 and parts[0] == "posts":
        if not auth:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "auth"})
        pid = parts[1]
        post = POSTS.get(pid)
        if not post:
            return 404, {"content-type": "application/json"}, json.dumps({"error": "not found"})
        if post["author"] != auth and USERS[auth]["role"] != "admin":
            return 403, {"content-type": "application/json"}, json.dumps({"error": "forbidden"})
        del POSTS[pid]
        for cid in list(COMMENTS.keys()):
            if COMMENTS[cid]["post"] == pid:
                del COMMENTS[cid]
        db.execute("DELETE FROM posts WHERE id=?", (pid,))
        return 204, {}, ""
    if method == "POST" and len(parts) == 3 and parts[0] == "posts" and parts[2] == "comments":
        if not auth:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "auth"})
        pid = parts[1]
        if pid not in POSTS:
            return 404, {"content-type": "application/json"}, json.dumps({"error": "no post"})
        text = parsed.get("text", "").strip()
        if not text or len(text) > 1000:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad text"})
        cid = hashlib.sha256((auth + text + str(now)).encode()).hexdigest()[:12]
        COMMENTS[cid] = {"id": cid, "post": pid, "author": auth, "text": text, "created": now}
        return 201, {"content-type": "application/json"}, json.dumps(COMMENTS[cid])
    if method == "GET" and parts == ["admin", "stats"]:
        if not auth or USERS[auth]["role"] != "admin":
            return 403, {"content-type": "application/json"}, json.dumps({"error": "forbidden"})
        return 200, {"content-type": "application/json"}, json.dumps({
            "users": len(USERS), "posts": len(POSTS),
            "comments": len(COMMENTS), "sessions": len(SESSIONS),
        })
    return 404, {"content-type": "application/json"}, json.dumps({"error": "no route"})
```
