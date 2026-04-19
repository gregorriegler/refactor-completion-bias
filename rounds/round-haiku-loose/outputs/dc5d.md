```python
import json
import hashlib
import time
from dataclasses import dataclass
from typing import Any, Tuple, Dict, Optional

# Constants
HTTP_HEADERS_JSON = {"content-type": "application/json"}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 100  # requests per window
TOKEN_EXPIRY = 3600  # seconds
PASSWORD_MIN_LENGTH = 8
TITLE_MAX_LENGTH = 200
CONTENT_MAX_LENGTH = 10000
COMMENT_MAX_LENGTH = 1000
ID_HASH_LENGTH = 12

# Global state
SESSIONS = {}
USERS = {"admin": {"pw": "adminhash", "role": "admin"}}
POSTS = {}
COMMENTS = {}
RATE_LIMIT = {}

Response = Tuple[int, Dict[str, str], str]


def json_response(status: int, data: Dict[str, Any]) -> Response:
    """Helper to create consistent JSON responses."""
    return status, HTTP_HEADERS_JSON, json.dumps(data)


def error_response(status: int, error: str) -> Response:
    """Helper for error responses."""
    return json_response(status, {"error": error})


class RateLimiter:
    """Rate limiting by IP address."""
    
    def __init__(self, window: int = RATE_LIMIT_WINDOW, limit: int = RATE_LIMIT_MAX):
        self.window = window
        self.limit = limit
        self.buckets = {}
    
    def check_and_record(self, ip: str, now: float) -> Optional[Response]:
        """Check rate limit and record request. Returns error response if limited."""
        bucket = self.buckets.setdefault(ip, [])
        bucket[:] = [t for t in bucket if now - t < self.window]
        
        if len(bucket) >= self.limit:
            return error_response(429, "rate limit")
        
        bucket.append(now)
        return None


class AuthHandler:
    """Authentication and authorization logic."""
    
    def __init__(self, sessions: Dict, users: Dict):
        self.sessions = sessions
        self.users = users
    
    def verify_token(self, headers: Dict, now: float) -> Optional[str]:
        """Extract and verify auth token. Returns username if valid."""
        if "authorization" not in headers:
            return None
        
        token = headers["authorization"].replace("Bearer ", "")
        sess = self.sessions.get(token)
        
        if sess and sess["expires"] > now:
            return sess["user"]
        return None
    
    def login(self, username: str, password: str, now: float) -> Response:
        """Authenticate user and create session."""
        if not username or not password:
            return error_response(400, "missing")
        
        user = self.users.get(username)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if not user or user["pw"] != password_hash:
            return error_response(401, "bad creds")
        
        token = hashlib.sha256((username + str(now)).encode()).hexdigest()
        self.sessions[token] = {"user": username, "expires": now + TOKEN_EXPIRY}
        
        return json_response(200, {"token": token})
    
    def logout(self, headers: Dict) -> Response:
        """Invalidate session token."""
        if "authorization" in headers:
            token = headers["authorization"].replace("Bearer ", "")
            self.sessions.pop(token, None)
        return 204, {}, ""
    
    def is_admin(self, username: str) -> bool:
        """Check if user has admin role."""
        return username in self.users and self.users[username]["role"] == "admin"


class UserHandler:
    """User registration logic."""
    
    def __init__(self, users: Dict, db):
        self.users = users
        self.db = db
    
    def register(self, username: str, password: str, email: str) -> Response:
        """Create new user account."""
        if not username or not password or not email:
            return error_response(400, "missing")
        
        if len(password) < PASSWORD_MIN_LENGTH:
            return error_response(400, "pw short")
        
        if "@" not in email:
            return error_response(400, "bad email")
        
        if username in self.users:
            return error_response(409, "exists")
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = {
            "pw": password_hash,
            "role": "user",
            "email": email
        }
        self.db.execute("INSERT INTO users(name,email) VALUES (?,?)", (username, email))
        
        return json_response(201, {"username": username})


class PostHandler:
    """Post CRUD operations."""
    
    def __init__(self, posts: Dict, comments: Dict, db, users: Dict):
        self.posts = posts
        self.comments = comments
        self.db = db
        self.users = users
    
    def list_posts(self, headers: Dict) -> Response:
        """List all posts with pagination."""
        limit = int(headers.get("x-limit", "20"))
        offset = int(headers.get("x-offset", "0"))
        
        items = sorted(
            self.posts.values(),
            key=lambda p: p["created"],
            reverse=True
        )
        page = items[offset:offset + limit]
        
        return json_response(200, {"items": page, "total": len(items)})
    
    def get_post(self, post_id: str) -> Response:
        """Get single post with comments."""
        post = self.posts.get(post_id)
        if not post:
            return error_response(404, "not found")
        
        comments = [
            c for c in self.comments.values()
            if c["post"] == post_id
        ]
        
        return json_response(200, {"post": post, "comments": comments})
    
    def create_post(self, author: str, title: str, content: str, now: float) -> Response:
        """Create new post."""
        if not title or len(title) > TITLE_MAX_LENGTH:
            return error_response(400, "bad title")
        
        if not content or len(content) > CONTENT_MAX_LENGTH:
            return error_response(400, "bad content")
        
        post_id = hashlib.sha256(
            (author + title + str(now)).encode()
        ).hexdigest()[:ID_HASH_LENGTH]
        
        post = {
            "id": post_id,
            "title": title,
            "content": content,
            "author": author,
            "created": now
        }
        
        self.posts[post_id] = post
        self.db.execute(
            "INSERT INTO posts(id,author,title) VALUES (?,?,?)",
            (post_id, author, title)
        )
        
        return json_response(201, post)
    
    def delete_post(self, post_id: str, auth: str) -> Response:
        """Delete post and associated comments."""
        post = self.posts.get(post_id)
        if not post:
            return error_response(404, "not found")
        
        # Check authorization
        is_author = post["author"] == auth
        is_admin = self.users[auth]["role"] == "admin"
        
        if not (is_author or is_admin):
            return error_response(403, "forbidden")
        
        del self.posts[post_id]
        
        # Delete associated comments
        for cid in list(self.comments.keys()):
            if self.comments[cid]["post"] == post_id:
                del self.comments[cid]
        
        self.db.execute("DELETE FROM posts WHERE id=?", (post_id,))
        
        return 204, {}, ""


class CommentHandler:
    """Comment operations."""
    
    def __init__(self, comments: Dict, posts: Dict):
        self.comments = comments
        self.posts = posts
    
    def create_comment(self, author: str, post_id: str, text: str, now: float) -> Response:
        """Create new comment on post."""
        if post_id not in self.posts:
            return error_response(404, "no post")
        
        text = text.strip()
        if not text or len(text) > COMMENT_MAX_LENGTH:
            return error_response(400, "bad text")
        
        comment_id = hashlib.sha256(
            (author + text + str(now)).encode()
        ).hexdigest()[:ID_HASH_LENGTH]
        
        comment = {
            "id": comment_id,
            "post": post_id,
            "author": author,
            "text": text,
            "created": now
        }
        
        self.comments[comment_id] = comment
        return json_response(201, comment)


class AdminHandler:
    """Admin operations."""
    
    def __init__(self, users: Dict):
        self.users = users
    
    def get_stats(self, auth: str, counts: Dict) -> Response:
        """Get system statistics."""
        if not auth or self.users[auth]["role"] != "admin":
            return error_response(403, "forbidden")
        
        return json_response(200, counts)


def handle_request(method, path, headers, body, db):
    """Route requests to appropriate handlers."""
    now = time.time()
    
    # Rate limiting
    rate_limiter = RateLimiter()
    ip = headers.get("x-forwarded-for", "unknown")
    rate_limit_error = rate_limiter.check_and_record(ip, now)
    if rate_limit_error:
        return rate_limit_error
    
    # Authentication
    auth_handler = AuthHandler(SESSIONS, USERS)
    auth = auth_handler.verify_token(headers, now)
    
    # Parse request body
    try:
        parsed = json.loads(body) if body else {}
    except Exception:
        return error_response(400, "bad json")
    
    parts = [p for p in path.split("/") if p]
    
    # Route handling
    if method == "POST" and parts == ["auth", "login"]:
        return auth_handler.login(parsed.get("username"), parsed.get("password"), now)
    
    if method == "POST" and parts == ["auth", "logout"]:
        return auth_handler.logout(headers)
    
    if method == "POST" and parts == ["users"]:
        user_handler = UserHandler(USERS, db)
        return user_handler.register(
            parsed.get("username"),
            parsed.get("password"),
            parsed.get("email")
        )
    
    post_handler = PostHandler(POSTS, COMMENTS, db, USERS)
    
    if method == "GET" and parts == ["posts"]:
        return post_handler.list_posts(headers)
    
    if method == "GET" and len(parts) == 2 and parts[0] == "posts":
        return post_handler.get_post(parts[1])
    
    if method == "POST" and parts == ["posts"]:
        if not auth:
            return error_response(401, "auth")
        return post_handler.create_post(
            auth,
            parsed.get("title"),
            parsed.get("content"),
            now
        )
    
    if method == "DELETE" and len(parts) == 2 and parts[0] == "posts":
        if not auth:
            return error_response(401, "auth")
        return post_handler.delete_post(parts[1], auth)
    
    comment_handler = CommentHandler(COMMENTS, POSTS)
    
    if method == "POST" and len(parts) == 3 and parts[0] == "posts" and parts[2] == "comments":
        if not auth:
            return error_response(401, "auth")
        return comment_handler.create_comment(
            auth,
            parts[1],
            parsed.get("text", ""),
            now
        )
    
    if method == "GET" and parts == ["admin", "stats"]:
        admin_handler = AdminHandler(USERS)
        counts = {
            "users": len(USERS),
            "posts": len(POSTS),
            "comments": len(COMMENTS),
            "sessions": len(SESSIONS),
        }
        return admin_handler.get_stats(auth, counts)
    
    return error_response(404, "no route")
```

Notes on refactoring:
- Extracted response helpers (`json_response`, `error_response`) to eliminate repeated boilerplate
- Broke monolithic function into focused handler classes (RateLimiter, AuthHandler, UserHandler, PostHandler, CommentHandler, AdminHandler)
- Extracted magic numbers into named constants at top
- Improved type hints with Response type alias
- Grouped related logic into classes for better maintainability
- Each handler class has a single responsibility
- Reduced code duplication in validation logic
- Made the main `handle_request` function much more readable as a router

