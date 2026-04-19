```python
import re
from typing import Any, Callable

# Token type definitions
WHITESPACE = {' ', '\t', '\n'}
OPERATORS = "+-*/()<>=,;"
KEYWORDS = {"if", "then", "else", "let", "in", "and", "or", "not", "true", "false"}
BUILTIN_FUNCS = {"min", "max", "abs", "len"}


def tokenize(src: str) -> list[tuple[str, Any]]:
    tokens = []
    i = 0
    
    while i < len(src):
        c = src[i]
        
        # Skip whitespace
        if c in WHITESPACE:
            i += 1
            continue
        
        # Handle operators
        if c in OPERATORS:
            if _match_operator(src, i, c, tokens):
                continue
            tokens.append(("op", c))
            i += 1
            continue
        
        # Handle numbers
        if c.isdigit():
            i = _consume_number(src, i, tokens)
            continue
        
        # Handle identifiers and keywords
        if c.isalpha() or c == "_":
            i = _consume_identifier(src, i, tokens)
            continue
        
        # Handle strings
        if c == '"':
            i = _consume_string(src, i, tokens)
            continue
        
        raise SyntaxError(f"bad char {c}")
    
    tokens.append(("eof", None))
    return tokens


def _match_operator(src: str, i: int, c: str, tokens: list) -> bool:
    """Try to match multi-char operators and add to tokens. Returns True if matched."""
    two_char_ops = {"==": ("=", "="), "<=": ("<", "="), ">=": (">", "=")}
    if c in two_char_ops and i + 1 < len(src):
        expected_next = two_char_ops[c][1]
        if src[i + 1] == expected_next:
            tokens.append(("op", c))
            return True
    return False


def _consume_number(src: str, start: int, tokens: list) -> int:
    """Consume a number token and add to tokens. Returns new position."""
    j = start
    while j < len(src) and (src[j].isdigit() or src[j] == "."):
        j += 1
    num_str = src[start:j]
    num = float(num_str) if "." in num_str else int(num_str)
    tokens.append(("num", num))
    return j


def _consume_identifier(src: str, start: int, tokens: list) -> int:
    """Consume an identifier or keyword token and add to tokens. Returns new position."""
    j = start
    while j < len(src) and (src[j].isalnum() or src[j] == "_"):
        j += 1
    word = src[start:j]
    token_type = "kw" if word in KEYWORDS else "id"
    tokens.append((token_type, word))
    return j


def _consume_string(src: str, start: int, tokens: list) -> int:
    """Consume a string token and add to tokens. Returns new position."""
    j = start + 1
    while j < len(src) and src[j] != '"':
        j += 1
    tokens.append(("str", src[start + 1 : j]))
    return j + 1


def evaluate(src: str, env: dict[str, Any] | None = None) -> Any:
    """Evaluate an expression in the given environment."""
    if env is None:
        env = {}
    
    tokens = tokenize(src)
    pos = [0]
    
    def peek() -> tuple:
        return tokens[pos[0]]
    
    def eat() -> tuple:
        t = tokens[pos[0]]
        pos[0] += 1
        return t
    
    def expect_token(token_type: str, token_val: str | None = None) -> None:
        """Verify and consume the expected token."""
        t = peek()
        if token_type == "kw":
            if not (t[0] == "kw" and t[1] == token_val):
                raise SyntaxError(f"expected {token_val}")
        elif token_type == "op":
            if not (t[0] == "op" and t[1] == token_val):
                raise SyntaxError(f"expected {token_val}")
        eat()
    
    def parse_expr() -> Any:
        # if-then-else
        if peek()[0] == "kw" and peek()[1] == "if":
            eat()
            cond = parse_expr()
            expect_token("kw", "then")
            a = parse_expr()
            expect_token("kw", "else")
            b = parse_expr()
            return a if _truthy(cond) else b
        
        # let-in
        if peek()[0] == "kw" and peek()[1] == "let":
            eat()
            if peek()[0] != "id":
                raise SyntaxError("expected id")
            name = eat()[1]
            expect_token("op", "=")
            val = parse_expr()
            expect_token("kw", "in")
            
            old_val = env.get(name)
            had_key = name in env
            env[name] = val
            try:
                return parse_expr()
            finally:
                if had_key:
                    env[name] = old_val
                else:
                    del env[name]
        
        return parse_or()
    
    def parse_or() -> Any:
        left = parse_and()
        while peek()[0] == "kw" and peek()[1] == "or":
            eat()
            right = parse_and()
            left = 1 if (_truthy(left) or _truthy(right)) else 0
        return left
    
    def parse_and() -> Any:
        left = parse_cmp()
        while peek()[0] == "kw" and peek()[1] == "and":
            eat()
            right = parse_cmp()
            left = 1 if (_truthy(left) and _truthy(right)) else 0
        return left
    
    def parse_cmp() -> Any:
        left = parse_add()
        if peek()[0] == "op" and peek()[1] in ("==", "<", ">", "<=", ">="):
            op = eat()[1]
            right = parse_add()
            cmp_ops = {
                "==": lambda l, r: l == r,
                "<": lambda l, r: l < r,
                ">": lambda l, r: l > r,
                "<=": lambda l, r: l <= r,
                ">=": lambda l, r: l >= r,
            }
            return 1 if cmp_ops[op](left, right) else 0
        return left
    
    def parse_add() -> Any:
        left = parse_mul()
        while peek()[0] == "op" and peek()[1] in ("+", "-"):
            op = eat()[1]
            right = parse_mul()
            if op == "+":
                left = str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right
            else:
                left = left - right
        return left
    
    def parse_mul() -> Any:
        left = parse_unary()
        while peek()[0] == "op" and peek()[1] in ("*", "/"):
            op = eat()[1]
            right = parse_unary()
            left = left * right if op == "*" else left / right
        return left
    
    def parse_unary() -> Any:
        if peek()[0] == "op" and peek()[1] == "-":
            eat()
            return -parse_unary()
        if peek()[0] == "kw" and peek()[1] == "not":
            eat()
            v = parse_unary()
            return 0 if _truthy(v) else 1
        return parse_atom()
    
    def parse_atom() -> Any:
        t = eat()
        
        if t[0] == "num":
            return t[1]
        if t[0] == "str":
            return t[1]
        if t[0] == "kw":
            if t[1] == "true":
                return 1
            if t[1] == "false":
                return 0
        
        if t[0] == "id":
            # Function call
            if peek()[0] == "op" and peek()[1] == "(":
                eat()
                args = []
                if not (peek()[0] == "op" and peek()[1] == ")"):
                    args.append(parse_expr())
                    while peek()[0] == "op" and peek()[1] == ",":
                        eat()
                        args.append(parse_expr())
                expect_token("op", ")")
                
                func_map = {
                    "min": min,
                    "max": max,
                    "abs": lambda x: abs(x[0]),
                    "len": lambda x: len(x[0]),
                }
                if t[1] not in func_map:
                    raise NameError(f"unknown fn {t[1]}")
                return func_map[t[1]](args)
            
            # Variable lookup
            if t[1] not in env:
                raise NameError(f"undefined {t[1]}")
            return env[t[1]]
        
        # Parenthesized expression
        if t[0] == "op" and t[1] == "(":
            v = parse_expr()
            expect_token("op", ")")
            return v
        
        raise SyntaxError(f"unexpected {t}")
    
    def _truthy(v: Any) -> bool:
        """Check if a value is truthy in this language."""
        return v not in (0, 0.0, "", None, False)
    
    return parse_expr()
```

Key improvements:
- Extracted tokenization helpers (`_match_operator`, `_consume_number`, `_consume_identifier`, `_consume_string`) to reduce repetition in `tokenize()`
- Added type hints for better code clarity
- Extracted constants for whitespace, operators, keywords, and builtin functions
- Refactored comparison operators to use a dictionary mapping instead of repeated if statements
- Simplified truthy logic into a single condition
- Added a helper `expect_token()` to reduce repeated token validation
- Improved error messages with f-strings
- Fixed the if-then-else line 78 bug (was `cond if False else ...`, now correctly evaluates condition)
- Extracted builtin function mapping to a dictionary for extensibility
- Better variable naming and organization of parser functions
