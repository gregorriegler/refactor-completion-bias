```python
import json
import hashlib
import time
from typing import Any

SESSIONS: dict[str, dict] = {}
USERS: dict[str, dict] = {"admin": {"pw": "adminhash", "role": "admin"}}
POSTS: dict[str, dict] = {}
COMMENTS: dict[str, dict] = {}
RATE_LIMIT: dict[str, list[float]] = {}

JSON_CONTENT = {"content-type": "application/json"}


def _json(data: Any) -> str:
    return json.dumps(data)


def ok(data: Any) -> tuple:
    return 200, JSON_CONTENT, _json(data)


def created(data: Any) -> tuple:
    return 201, JSON_CONTENT, _json(data)


def no_content() -> tuple:
    return 204, {}, ""


def error(status: int, message: str) -> tuple:
    return status, JSON_CONTENT, _json({"error": message})


def _check_rate_limit(ip: str, now: float) -> bool:
    bucket = RATE_LIMIT.setdefault(ip, [])
    bucket[:] = [t for t in bucket if now - t < 60]
    if len(bucket) >= 100:
        return False
    bucket.append(now)
    return True


def _resolve_session(headers: dict, now: float) -> str | None:
    auth_header = headers.get("authorization", "")
    if not auth_header:
        return None
    token = auth_header.removeprefix("Bearer ")
    sess = SESSIONS.get(token)
    if sess and sess["expires"] > now:
        return sess["user"]
    return None


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _require_auth(auth: str | None) -> tuple | None:
    if not auth:
        return error(401, "auth required")
    return None


def _require_admin(auth: str | None) -> tuple | None:
    if not auth or USERS.get(auth, {}).get("role") != "admin":
        return error(403, "forbidden")
    return None


# --- Route handlers ---

def handle_login(parsed: dict, now: float) -> tuple:
    username = parsed.get("username")
    password = parsed.get("password")
    if not username or not password:
        return error(400, "missing username or password")
    user = USERS.get(username)
    if not user or user["pw"] != _hash(password):
        return error(401, "bad credentials")
    token = _hash(username + str(now))
    SESSIONS[token] = {"user": username, "expires": now + 3600}
    return created({"token": token})


def handle_logout(headers: dict) -> tuple:
    auth_header = headers.get("authorization", "")
    if auth_header:
        token = auth_header.removeprefix("Bearer ")
        SESSIONS.pop(token, None)
    return no_content()


def handle_register(parsed: dict, db: Any) -> tuple:
    username = parsed.get("username")
    password = parsed.get("password")
    email = parsed.get("email")
    if not username or not password or not email:
        return error(400, "missing fields")
    if len(password) < 8:
        return error(400, "password too short")
    if "@" not in email:
        return error(400, "invalid email")
    if username in USERS:
        return error(409, "username already exists")
    USERS[username] = {"pw": _hash(password), "role": "user", "email": email}
    db.execute("INSERT INTO users(name,email) VALUES (?,?)", (username, email))
    return created({"username": username})


def handle_list_posts(headers: dict) -> tuple:
    limit = int(headers.get("x-limit", "20"))
    offset = int(headers.get("x-offset", "0"))
    items = sorted(POSTS.values(), key=lambda p: p["created"], reverse=True)
    page = items[offset : offset + limit]
    return ok({"items": page, "total": len(items)})


def handle_get_post(post_id: str) -> tuple:
    post = POSTS.get(post_id)
    if not post:
        return error(404, "post not found")
    comments = [c for c in COMMENTS.values() if c["post"] == post_id]
    return ok({"post": post, "comments": comments})


def handle_create_post(parsed: dict, auth: str, now: float, db: Any) -> tuple:
    title = parsed.get("title")
    content = parsed.get("content")
    if not title or len(title) > 200:
        return error(400, "invalid title (must be 1–200 chars)")
    if not content or len(content) > 10000:
        return error(400, "invalid content (must be 1–10000 chars)")
    post_id = _hash(auth + title + str(now))[:12]
    post = {"id": post_id, "title": title, "content": content, "author": auth, "created": now}
    POSTS[post_id] = post
    db.execute("INSERT INTO posts(id,author,title) VALUES (?,?,?)", (post_id, auth, title))
    return created(post)


def handle_delete_post(post_id: str, auth: str, db: Any) -> tuple:
    post = POSTS.get(post_id)
    if not post:
        return error(404, "post not found")
    if post["author"] != auth and USERS[auth]["role"] != "admin":
        return error(403, "forbidden")
    del POSTS[post_id]
    for cid in [cid for cid, c in COMMENTS.items() if c["post"] == post_id]:
        del COMMENTS[cid]
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    return no_content()


def handle_create_comment(post_id: str, parsed: dict, auth: str, now: float) -> tuple:
    if post_id not in POSTS:
        return error(404, "post not found")
    text = parsed.get("text", "").strip()
    if not text or len(text) > 1000:
        return error(400, "invalid comment text (must be 1–1000 chars)")
    cid = _hash(auth + text + str(now))[:12]
    comment = {"id": cid, "post": post_id, "author": auth, "text": text, "created": now}
    COMMENTS[cid] = comment
    return created(comment)


def handle_admin_stats(auth: str | None) -> tuple:
    if denied := _require_admin(auth):
        return denied
    return ok({
        "users": len(USERS),
        "posts": len(POSTS),
        "comments": len(COMMENTS),
        "sessions": len(SESSIONS),
    })


# --- Dispatcher ---

def handle_request(
    method: str,
    path: str,
    headers: dict,
    body: str,
    db: Any,
) -> tuple:
    now = time.time()
    ip = headers.get("x-forwarded-for", "unknown")

    if not _check_rate_limit(ip, now):
        return error(429, "rate limit exceeded")

    auth = _resolve_session(headers, now)

    try:
        parsed = json.loads(body) if body else {}
    except Exception:
        return error(400, "invalid JSON body")

    parts = [p for p in path.split("/") if p]

    match (method, parts):
        case ("POST", ["auth", "login"]):
            return handle_login(parsed, now)

        case ("POST", ["auth", "logout"]):
            return handle_logout(headers)

        case ("POST", ["users"]):
            return handle_register(parsed, db)

        case ("GET", ["posts"]):
            return handle_list_posts(headers)

        case ("GET", ["posts", post_id]):
            return handle_get_post(post_id)

        case ("POST", ["posts"]):
            if denied := _require_auth(auth):
                return denied
            return handle_create_post(parsed, auth, now, db)

        case ("DELETE", ["posts", post_id]):
            if denied := _require_auth(auth):
                return denied
            return handle_delete_post(post_id, auth, db)

        case ("POST", ["posts", post_id, "comments"]):
            if denied := _require_auth(auth):
                return denied
            return handle_create_comment(post_id, parsed, auth, now)

        case ("GET", ["admin", "stats"]):
            return handle_admin_stats(auth)

        case _:
            return error(404, "no matching route")
```

Key changes:

- Extracted each route into its own focused handler function (`handle_login`, `handle_register`, `handle_list_posts`, etc.), eliminating the flat chain of `if` branches.
- Replaced repeated `(status, {"content-type": "application/json"}, json.dumps(...))` tuples with small helpers: `ok`, `created`, `no_content`, and `error`.
- Introduced `_check_rate_limit` and `_resolve_session` to isolate cross-cutting concerns from routing logic.
- Added `_require_auth` and `_require_admin` guard helpers that return an error tuple or `None`, enabling the walrus-operator pattern `if denied := _require_auth(auth): return denied`.
- Replaced the chain of `if method == ... and parts == ...` conditions with a `match` statement, making the routing table immediately scannable.
- Replaced `str.replace("Bearer ", "")` with `str.removeprefix("Bearer ")` to avoid accidentally stripping mid-string occurrences.
- Added type annotations throughout and named the module-level stores with explicit `dict` types.
- Comment deletion in `handle_delete_post` now builds the list of IDs to remove before iterating, avoiding mutation-during-iteration issues.
