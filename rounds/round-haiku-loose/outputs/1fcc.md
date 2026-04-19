```python
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
import json
import hashlib
import time


# Constants
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 100
SESSION_EXPIRY_SECONDS = 3600
MIN_PASSWORD_LENGTH = 8
MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 10000
MAX_COMMENT_LENGTH = 1000
HASH_TRUNCATE_LENGTH = 12


class UserRole(Enum):
    """User roles in the system."""
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    """User account data."""
    username: str
    password_hash: str
    role: UserRole
    email: str = ""


@dataclass
class Session:
    """Authentication session."""
    user: str
    expires: float


@dataclass
class Post:
    """Post data."""
    id: str
    title: str
    content: str
    author: str
    created: float


@dataclass
class Comment:
    """Comment on a post."""
    id: str
    post: str
    author: str
    text: str
    created: float


@dataclass
class ApiResponse:
    """Standard API response."""
    status_code: int
    headers: dict[str, str]
    body: str


class AuthorizationError(Exception):
    """Raised when authentication fails or is missing."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class NotFoundError(Exception):
    """Raised when a resource is not found."""
    pass


class ConflictError(Exception):
    """Raised when a resource already exists."""
    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class Database:
    """Simple database interface."""
    def __init__(self):
        self.conn = None
    
    def execute(self, query: str, params: tuple) -> None:
        """Execute a database query."""
        # Placeholder for actual database implementation
        pass


class ApiHandler:
    """Handles HTTP requests for a simple REST API."""
    
    def __init__(self, db: Database):
        self.db = db
        self.sessions: dict[str, Session] = {}
        self.users: dict[str, User] = {
            "admin": User(
                username="admin",
                password_hash="adminhash",
                role=UserRole.ADMIN
            )
        }
        self.posts: dict[str, Post] = {}
        self.comments: dict[str, Comment] = {}
        self.rate_limits: dict[str, list[float]] = {}
    
    def handle_request(self, method: str, path: str, headers: dict[str, str], body: str) -> ApiResponse:
        """Route and handle an HTTP request."""
        now = time.time()
        
        # Check rate limit
        self._check_rate_limit(headers, now)
        
        # Extract authentication
        auth = self._extract_auth(headers, now)
        
        # Parse request body
        parsed = self._parse_body(body)
        
        # Parse path
        parts = [p for p in path.split("/") if p]
        
        # Route to handler
        if method == "POST" and parts == ["auth", "login"]:
            return self._handle_login(parsed, now)
        elif method == "POST" and parts == ["auth", "logout"]:
            return self._handle_logout(headers)
        elif method == "POST" and parts == ["users"]:
            return self._handle_user_creation(parsed)
        elif method == "GET" and parts == ["posts"]:
            return self._handle_list_posts(headers)
        elif method == "GET" and len(parts) == 2 and parts[0] == "posts":
            return self._handle_get_post(parts[1])
        elif method == "POST" and parts == ["posts"]:
            return self._handle_create_post(parsed, auth, now)
        elif method == "DELETE" and len(parts) == 2 and parts[0] == "posts":
            return self._handle_delete_post(parts[1], auth)
        elif method == "POST" and len(parts) == 3 and parts[:3] == ["posts", parts[1], "comments"]:
            return self._handle_create_comment(parts[1], parsed, auth, now)
        elif method == "GET" and parts == ["admin", "stats"]:
            return self._handle_admin_stats(auth)
        else:
            return self._error_response(404, "no route")
    
    def _check_rate_limit(self, headers: dict[str, str], now: float) -> None:
        """Check if the request exceeds rate limit."""
        ip = headers.get("x-forwarded-for", "unknown")
        bucket = self.rate_limits.setdefault(ip, [])
        
        # Remove old timestamps outside the window
        bucket[:] = [t for t in bucket if now - t < RATE_LIMIT_WINDOW_SECONDS]
        
        if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
            raise RateLimitError("rate limit")
        
        bucket.append(now)
    
    def _extract_auth(self, headers: dict[str, str], now: float) -> str | None:
        """Extract and validate authentication token."""
        if "authorization" not in headers:
            return None
        
        token = headers["authorization"].replace("Bearer ", "")
        session = self.sessions.get(token)
        
        if session and session.expires > now:
            return session.user
        
        return None
    
    def _parse_body(self, body: str) -> dict[str, Any]:
        """Parse JSON body, raising ValidationError on failure."""
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise ValidationError("bad json")
    
    def _require_auth(self, auth: str | None) -> str:
        """Ensure user is authenticated, return username."""
        if not auth:
            raise AuthorizationError("auth")
        return auth
    
    def _require_admin(self, auth: str) -> None:
        """Ensure user is an admin."""
        user = self.users.get(auth)
        if not user or user.role != UserRole.ADMIN:
            raise AuthorizationError("forbidden")
    
    def _handle_login(self, parsed: dict[str, Any], now: float) -> ApiResponse:
        """Handle POST /auth/login."""
        username = parsed.get("username")
        password = parsed.get("password")
        
        if not username or not password:
            raise ValidationError("missing")
        
        user = self.users.get(username)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if not user or user.password_hash != password_hash:
            raise AuthorizationError("bad creds")
        
        token = hashlib.sha256((username + str(now)).encode()).hexdigest()
        self.sessions[token] = Session(user=username, expires=now + SESSION_EXPIRY_SECONDS)
        
        return self._success_response(200, {"token": token})
    
    def _handle_logout(self, headers: dict[str, str]) -> ApiResponse:
        """Handle POST /auth/logout."""
        if "authorization" in headers:
            token = headers["authorization"].replace("Bearer ", "")
            self.sessions.pop(token, None)
        
        return ApiResponse(status_code=204, headers={}, body="")
    
    def _handle_user_creation(self, parsed: dict[str, Any]) -> ApiResponse:
        """Handle POST /users."""
        username = parsed.get("username")
        password = parsed.get("password")
        email = parsed.get("email")
        
        if not username or not password or not email:
            raise ValidationError("missing")
        
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError("pw short")
        
        if "@" not in email:
            raise ValidationError("bad email")
        
        if username in self.users:
            raise ConflictError("exists")
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = User(
            username=username,
            password_hash=password_hash,
            role=UserRole.USER,
            email=email
        )
        self.db.execute("INSERT INTO users(name,email) VALUES (?,?)", (username, email))
        
        return self._success_response(201, {"username": username})
    
    def _handle_list_posts(self, headers: dict[str, str]) -> ApiResponse:
        """Handle GET /posts."""
        limit = int(headers.get("x-limit", "20"))
        offset = int(headers.get("x-offset", "0"))
        
        items = sorted(
            self.posts.values(),
            key=lambda p: p.created,
            reverse=True
        )
        page = items[offset:offset + limit]
        
        return self._success_response(200, {
            "items": [self._post_to_dict(p) for p in page],
            "total": len(items)
        })
    
    def _handle_get_post(self, post_id: str) -> ApiResponse:
        """Handle GET /posts/{id}."""
        post = self.posts.get(post_id)
        if not post:
            raise NotFoundError("not found")
        
        comments = [
            self._comment_to_dict(c)
            for c in self.comments.values()
            if c.post == post_id
        ]
        
        return self._success_response(200, {
            "post": self._post_to_dict(post),
            "comments": comments
        })
    
    def _handle_create_post(self, parsed: dict[str, Any], auth: str | None, now: float) -> ApiResponse:
        """Handle POST /posts."""
        auth = self._require_auth(auth)
        
        title = parsed.get("title", "")
        content = parsed.get("content", "")
        
        if not title or len(title) > MAX_TITLE_LENGTH:
            raise ValidationError("bad title")
        
        if not content or len(content) > MAX_CONTENT_LENGTH:
            raise ValidationError("bad content")
        
        post_id = hashlib.sha256(
            (auth + title + str(now)).encode()
        ).hexdigest()[:HASH_TRUNCATE_LENGTH]
        
        post = Post(
            id=post_id,
            title=title,
            content=content,
            author=auth,
            created=now
        )
        self.posts[post_id] = post
        self.db.execute(
            "INSERT INTO posts(id,author,title) VALUES (?,?,?)",
            (post_id, auth, title)
        )
        
        return self._success_response(201, self._post_to_dict(post))
    
    def _handle_delete_post(self, post_id: str, auth: str | None) -> ApiResponse:
        """Handle DELETE /posts/{id}."""
        auth = self._require_auth(auth)
        
        post = self.posts.get(post_id)
        if not post:
            raise NotFoundError("not found")
        
        # Check authorization
        if post.author != auth:
            self._require_admin(auth)
        
        del self.posts[post_id]
        
        # Delete associated comments
        for cid in list(self.comments.keys()):
            if self.comments[cid].post == post_id:
                del self.comments[cid]
        
        self.db.execute("DELETE FROM posts WHERE id=?", (post_id,))
        
        return ApiResponse(status_code=204, headers={}, body="")
    
    def _handle_create_comment(self, post_id: str, parsed: dict[str, Any], auth: str | None, now: float) -> ApiResponse:
        """Handle POST /posts/{id}/comments."""
        auth = self._require_auth(auth)
        
        if post_id not in self.posts:
            raise NotFoundError("no post")
        
        text = parsed.get("text", "").strip()
        
        if not text or len(text) > MAX_COMMENT_LENGTH:
            raise ValidationError("bad text")
        
        comment_id = hashlib.sha256(
            (auth + text + str(now)).encode()
        ).hexdigest()[:HASH_TRUNCATE_LENGTH]
        
        comment = Comment(
            id=comment_id,
            post=post_id,
            author=auth,
            text=text,
            created=now
        )
        self.comments[comment_id] = comment
        
        return self._success_response(201, self._comment_to_dict(comment))
    
    def _handle_admin_stats(self, auth: str | None) -> ApiResponse:
        """Handle GET /admin/stats."""
        auth = self._require_auth(auth)
        self._require_admin(auth)
        
        return self._success_response(200, {
            "users": len(self.users),
            "posts": len(self.posts),
            "comments": len(self.comments),
            "sessions": len(self.sessions),
        })
    
    def _success_response(self, status_code: int, data: dict[str, Any]) -> ApiResponse:
        """Create a successful JSON response."""
        return ApiResponse(
            status_code=status_code,
            headers={"content-type": "application/json"},
            body=json.dumps(data)
        )
    
    def _error_response(self, status_code: int, error: str) -> ApiResponse:
        """Create an error JSON response."""
        return self._success_response(status_code, {"error": error})
    
    def _post_to_dict(self, post: Post) -> dict[str, Any]:
        """Convert post to dictionary."""
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author": post.author,
            "created": post.created,
        }
    
    def _comment_to_dict(self, comment: Comment) -> dict[str, Any]:
        """Convert comment to dictionary."""
        return {
            "id": comment.id,
            "post": comment.post,
            "author": comment.author,
            "text": comment.text,
            "created": comment.created,
        }


def handle_request(method: str, path: str, headers: dict[str, str], body: str, db: Database) -> tuple[int, dict[str, str], str]:
    """
    Legacy interface adapter for the original function signature.
    
    Maps exceptions to appropriate HTTP responses.
    """
    handler = ApiHandler(db)
    
    try:
        response = handler.handle_request(method, path, headers, body)
        return response.status_code, response.headers, response.body
    except RateLimitError as e:
        return 429, {"content-type": "application/json"}, json.dumps({"error": str(e)})
    except ValidationError as e:
        return 400, {"content-type": "application/json"}, json.dumps({"error": str(e)})
    except AuthorizationError as e:
        status = 403 if str(e) == "forbidden" else 401
        return status, {"content-type": "application/json"}, json.dumps({"error": str(e)})
    except NotFoundError as e:
        return 404, {"content-type": "application/json"}, json.dumps({"error": str(e)})
    except ConflictError as e:
        return 409, {"content-type": "application/json"}, json.dumps({"error": str(e)})
```

## Refactoring Notes

**Key improvements:**

1. **Extracted constants**: All magic numbers and strings are now named constants at the top (RATE_LIMIT_WINDOW_SECONDS, SESSION_EXPIRY_SECONDS, etc.)

2. **Custom exceptions**: Created domain-specific exception classes (AuthorizationError, ValidationError, NotFoundError, etc.) that map cleanly to HTTP status codes

3. **Data classes**: Replaced dictionaries with proper dataclasses (User, Session, Post, Comment, ApiResponse) for type safety and clarity

4. **Separation of concerns**: 
   - ApiHandler class encapsulates all the request handling logic
   - Each endpoint has its own private handler method (_handle_*)
   - Utility methods for common operations (_check_rate_limit, _require_auth, _parse_body, etc.)

5. **Removed repetition**: 
   - Centralized error response formatting in _error_response and _success_response
   - Created helper methods for post/comment serialization
   - Rate limit logic is now reusable

6. **Better error handling**: Proper exception flow instead of scattered error returns throughout the function

7. **Enums**: UserRole is now an enum instead of magic strings

8. **Testability**: Each handler method is now independently testable and can be called in isolation

9. **Backward compatibility**: The legacy `handle_request` function wraps the new ApiHandler to maintain the original interface and map exceptions to HTTP responses

10. **Type hints**: Comprehensive type annotations throughout for clarity and IDE support

**Notes on design decisions:**
- The ApiHandler now owns the data stores (sessions, users, posts, comments) which would enable future improvements like dependency injection and better testability
- Exception-based flow makes the happy path clear and keeps handler methods concise
- Separate private handler methods make the main routing logic in handle_request very readable
- The legacy adapter at the bottom ensures backward compatibility with existing code that calls the original handle_request signature
