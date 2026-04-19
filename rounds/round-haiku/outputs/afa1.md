```python
import json
import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

SESSIONS = {}
USERS = {"admin": {"pw": "adminhash", "role": "admin"}}
POSTS = {}
COMMENTS = {}
RATE_LIMIT = {}

# Constants
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 100
SESSION_DURATION = 3600
MIN_PASSWORD_LENGTH = 8
MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 10000
MAX_COMMENT_LENGTH = 1000
MAX_EMAIL_LENGTH = 100
JSON_CONTENT_TYPE = {"content-type": "application/json"}


@dataclass
class Response:
    status: int
    headers: Dict[str, str]
    body: str

    def to_tuple(self) -> Tuple[int, Dict[str, str], str]:
        return self.status, self.headers, self.body


def error_response(status: int, message: str) -> Response:
    """Create a standardized error response."""
    return Response(status, JSON_CONTENT_TYPE, json.dumps({"error": message}))


def success_response(status: int, data: Any) -> Response:
    """Create a standardized success response."""
    return Response(status, JSON_CONTENT_TYPE, json.dumps(data))


def check_rate_limit(ip: str, now: float) -> Optional[Response]:
    """Check and update rate limit for IP. Returns error response if rate limited."""
    bucket = RATE_LIMIT.setdefault(ip, [])
    bucket[:] = [t for t in bucket if now - t < RATE_LIMIT_WINDOW]
    if len(bucket) >= RATE_LIMIT_MAX:
        return error_response(429, "rate limit")
    bucket.append(now)
    return None


def get_auth_user(headers: Dict[str, str], now: float) -> Optional[str]:
    """Extract authenticated user from headers. Returns username or None."""
    if "authorization" not in headers:
        return None
    token = headers["authorization"].replace("Bearer ", "")
    sess = SESSIONS.get(token)
    if sess and sess["expires"] > now:
        return sess["user"]
    return None


def parse_path(path: str) -> List[str]:
    """Parse path into components."""
    return [p for p in path.split("/") if p]


def validate_login(parsed: Dict) -> Optional[Response]:
    """Validate login request payload."""
    if not parsed.get("username") or not parsed.get("password"):
        return error_response(400, "missing")
    return None


def handle_login(parsed: Dict, now: float) -> Response:
    """Handle login request."""
    validation_error = validate_login(parsed)
    if validation_error:
        return validation_error
    
    u = parsed["username"]
    p = parsed["password"]
    user = USERS.get(u)
    h = hashlib.sha256(p.encode()).hexdigest()
    
    if not user or user["pw"] != h:
        return error_response(401, "bad creds")
    
    token = hashlib.sha256((u + str(now)).encode()).hexdigest()
    SESSIONS[token] = {"user": u, "expires": now + SESSION_DURATION}
    return success_response(200, {"token": token})


def handle_logout(headers: Dict) -> Response:
    """Handle logout request."""
    if "authorization" in headers:
        tok = headers["authorization"].replace("Bearer ", "")
        SESSIONS.pop(tok, None)
    return Response(204, {}, "")


def validate_user_creation(parsed: Dict) -> Optional[Response]:
    """Validate user creation payload."""
    u = parsed.get("username")
    p = parsed.get("password")
    e = parsed.get("email")
    
    if not u or not p or not e:
        return error_response(400, "missing")
    if len(p) < MIN_PASSWORD_LENGTH:
        return error_response(400, "pw short")
    if "@" not in e:
        return error_response(400, "bad email")
    if u in USERS:
        return error_response(409, "exists")
    return None


def handle_user_creation(parsed: Dict, db) -> Response:
    """Handle user creation request."""
    validation_error = validate_user_creation(parsed)
    if validation_error:
        return validation_error
    
    u = parsed["username"]
    p = parsed["password"]
    e = parsed["email"]
    
    USERS[u] = {
        "pw": hashlib.sha256(p.encode()).hexdigest(),
        "role": "user",
        "email": e
    }
    db.execute("INSERT INTO users(name,email) VALUES (?,?)", (u, e))
    return success_response(201, {"username": u})


def handle_list_posts(headers: Dict) -> Response:
    """Handle listing posts."""
    limit = int(headers.get("x-limit", "20"))
    offset = int(headers.get("x-offset", "0"))
    items = sorted(POSTS.values(), key=lambda p: p["created"], reverse=True)
    page = items[offset:offset + limit]
    return success_response(200, {"items": page, "total": len(items)})


def handle_get_post(post_id: str) -> Response:
    """Handle getting a specific post with its comments."""
    post = POSTS.get(post_id)
    if not post:
        return error_response(404, "not found")
    comments = [c for c in COMMENTS.values() if c["post"] == post_id]
    return success_response(200, {"post": post, "comments": comments})


def validate_post_creation(parsed: Dict) -> Optional[Response]:
    """Validate post creation payload."""
    title = parsed.get("title")
    content = parsed.get("content")
    
    if not title or len(title) > MAX_TITLE_LENGTH:
        return error_response(400, "bad title")
    if not content or len(content) > MAX_CONTENT_LENGTH:
        return error_response(400, "bad content")
    return None


def handle_create_post(parsed: Dict, auth: str, now: float, db) -> Response:
    """Handle post creation."""
    if not auth:
        return error_response(401, "auth")
    
    validation_error = validate_post_creation(parsed)
    if validation_error:
        return validation_error
    
    title = parsed["title"]
    content = parsed["content"]
    pid = hashlib.sha256((auth + title + str(now)).encode()).hexdigest()[:12]
    
    POSTS[pid] = {
        "id": pid,
        "title": title,
        "content": content,
        "author": auth,
        "created": now
    }
    db.execute("INSERT INTO posts(id,author,title) VALUES (?,?,?)", (pid, auth, title))
    return success_response(201, POSTS[pid])


def handle_delete_post(post_id: str, auth: Optional[str], now: float, db) -> Response:
    """Handle post deletion."""
    if not auth:
        return error_response(401, "auth")
    
    post = POSTS.get(post_id)
    if not post:
        return error_response(404, "not found")
    
    is_author = post["author"] == auth
    is_admin = USERS[auth]["role"] == "admin"
    
    if not is_author and not is_admin:
        return error_response(403, "forbidden")
    
    del POSTS[post_id]
    for cid in list(COMMENTS.keys()):
        if COMMENTS[cid]["post"] == post_id:
            del COMMENTS[cid]
    
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    return Response(204, {}, "")


def validate_comment_creation(parsed: Dict) -> Optional[Response]:
    """Validate comment creation payload."""
    text = parsed.get("text", "").strip()
    if not text or len(text) > MAX_COMMENT_LENGTH:
        return error_response(400, "bad text")
    return None


def handle_create_comment(post_id: str, parsed: Dict, auth: str, now: float) -> Response:
    """Handle comment creation."""
    if not auth:
        return error_response(401, "auth")
    
    if post_id not in POSTS:
        return error_response(404, "no post")
    
    validation_error = validate_comment_creation(parsed)
    if validation_error:
        return validation_error
    
    text = parsed.get("text", "").strip()
    cid = hashlib.sha256((auth + text + str(now)).encode()).hexdigest()[:12]
    
    COMMENTS[cid] = {
        "id": cid,
        "post": post_id,
        "author": auth,
        "text": text,
        "created": now
    }
    return success_response(201, COMMENTS[cid])


def handle_admin_stats(auth: Optional[str]) -> Response:
    """Handle admin stats request."""
    if not auth or USERS[auth]["role"] != "admin":
        return error_response(403, "forbidden")
    
    return success_response(200, {
        "users": len(USERS),
        "posts": len(POSTS),
        "comments": len(COMMENTS),
        "sessions": len(SESSIONS),
    })


def handle_request(method, path, headers, body, db):
    now = time.time()
    ip = headers.get("x-forwarded-for", "unknown")
    
    # Check rate limit
    rate_limit_error = check_rate_limit(ip, now)
    if rate_limit_error:
        return rate_limit_error.to_tuple()
    
    # Parse request
    try:
        parsed = json.loads(body) if body else {}
    except Exception:
        return error_response(400, "bad json").to_tuple()
    
    auth = get_auth_user(headers, now)
    parts = parse_path(path)
    
    # Route handling
    if method == "POST" and parts == ["auth", "login"]:
        return handle_login(parsed, now).to_tuple()
    
    if method == "POST" and parts == ["auth", "logout"]:
        return handle_logout(headers).to_tuple()
    
    if method == "POST" and parts == ["users"]:
        return handle_user_creation(parsed, db).to_tuple()
    
    if method == "GET" and parts == ["posts"]:
        return handle_list_posts(headers).to_tuple()
    
    if method == "GET" and len(parts) == 2 and parts[0] == "posts":
        return handle_get_post(parts[1]).to_tuple()
    
    if method == "POST" and parts == ["posts"]:
        return handle_create_post(parsed, auth, now, db).to_tuple()
    
    if method == "DELETE" and len(parts) == 2 and parts[0] == "posts":
        return handle_delete_post(parts[1], auth, now, db).to_tuple()
    
    if method == "POST" and len(parts) == 3 and parts[0] == "posts" and parts[2] == "comments":
        return handle_create_comment(parts[1], parsed, auth, now).to_tuple()
    
    if method == "GET" and parts == ["admin", "stats"]:
        return handle_admin_stats(auth).to_tuple()
    
    return error_response(404, "no route").to_tuple()
```

## Refactoring notes:

**Key improvements:**
1. **Extracted constants** - Magic numbers moved to named module-level constants
2. **Created helper functions** - Rate limiting, auth extraction, path parsing are now reusable
3. **Response abstraction** - Standardized error/success responses with a `Response` dataclass, reducing duplication from ~50+ `return` statements with duplicated JSON formatting
4. **Handler functions** - Each route is now a separate, focused function instead of a giant monolithic handler with deep nesting
5. **Validation separation** - Input validation extracted into dedicated functions
6. **Reduced nesting** - Extracted handler functions flatten the control flow significantly
7. **Type hints** - Added type annotations for clarity and maintainability
