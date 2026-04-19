```python
import re
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

class TokenType(Enum):
    OP = "op"
    NUM = "num"
    STR = "str"
    KW = "kw"
    ID = "id"
    EOF = "eof"

class Token(Tuple[str, Any]):
    pass

KEYWORDS = {"if", "then", "else", "let", "in", "and", "or", "not", "true", "false"}
OPERATORS = "+-*/()<>=,;"
OPERATOR_MAP = {
    ("=", "="): "==",
    ("<", "="): "<=",
    (">", "="): ">=",
}
BUILTIN_FUNCTIONS = {"min": min, "max": max, "abs": abs, "len": len}

def tokenize(src: str) -> List[Token]:
    """Tokenize source code into a list of (type, value) tuples."""
    tokens = []
    i = 0
    
    while i < len(src):
        c = src[i]
        
        # Skip whitespace
        if c in " \t\n":
            i += 1
            continue
        
        # Handle operators
        if c in OPERATORS:
            op = _parse_operator(src, i)
            tokens.append((TokenType.OP.value, op["value"]))
            i = op["end"]
            continue
        
        # Handle numbers
        if c.isdigit():
            num = _parse_number(src, i)
            tokens.append((TokenType.NUM.value, num["value"]))
            i = num["end"]
            continue
        
        # Handle identifiers and keywords
        if c.isalpha() or c == "_":
            word = _parse_identifier(src, i)
            token_type = TokenType.KW.value if word["value"] in KEYWORDS else TokenType.ID.value
            tokens.append((token_type, word["value"]))
            i = word["end"]
            continue
        
        # Handle strings
        if c == '"':
            string = _parse_string(src, i)
            tokens.append((TokenType.STR.value, string["value"]))
            i = string["end"]
            continue
        
        raise SyntaxError(f"bad char {c}")
    
    tokens.append((TokenType.EOF.value, None))
    return tokens

def _parse_operator(src: str, start: int) -> Dict[str, Any]:
    """Parse a single or double-character operator."""
    c = src[start]
    if start + 1 < len(src) and (c, src[start + 1]) in OPERATOR_MAP:
        return {"value": OPERATOR_MAP[(c, src[start + 1])], "end": start + 2}
    return {"value": c, "end": start + 1}

def _parse_number(src: str, start: int) -> Dict[str, Any]:
    """Parse a numeric literal."""
    j = start
    while j < len(src) and (src[j].isdigit() or src[j] == "."):
        j += 1
    num_str = src[start:j]
    value = float(num_str) if "." in num_str else int(num_str)
    return {"value": value, "end": j}

def _parse_identifier(src: str, start: int) -> Dict[str, Any]:
    """Parse an identifier or keyword."""
    j = start
    while j < len(src) and (src[j].isalnum() or src[j] == "_"):
        j += 1
    return {"value": src[start:j], "end": j}

def _parse_string(src: str, start: int) -> Dict[str, Any]:
    """Parse a string literal."""
    j = start + 1
    while j < len(src) and src[j] != '"':
        j += 1
    return {"value": src[start + 1:j], "end": j + 1}

def _is_truthy(value: Any) -> bool:
    """Evaluate truthiness of a value."""
    return value not in (0, 0.0, "", None, False)

def evaluate(src: str, env: Optional[Dict[str, Any]] = None) -> Any:
    """Evaluate an expression in the given environment."""
    if env is None:
        env = {}
    
    tokens = tokenize(src)
    pos = [0]
    
    def peek() -> Token:
        return tokens[pos[0]]
    
    def eat() -> Token:
        t = tokens[pos[0]]
        pos[0] += 1
        return t
    
    def expect(token_type: str, value: Optional[str] = None) -> Token:
        """Expect and consume a specific token."""
        t = peek()
        if t[0] != token_type or (value is not None and t[1] != value):
            raise SyntaxError(f"expected {value or token_type}")
        return eat()
    
    def parse_expr() -> Any:
        """Parse an if/let expression or fallback to parse_or."""
        if peek()[0] == TokenType.KW.value and peek()[1] == "if":
            return _parse_if(eat, peek, expect, parse_expr)
        if peek()[0] == TokenType.KW.value and peek()[1] == "let":
            return _parse_let(eat, peek, expect, parse_expr, env)
        return parse_or()
    
    def parse_or() -> Any:
        """Parse OR expressions."""
        left = parse_and()
        while peek()[0] == TokenType.KW.value and peek()[1] == "or":
            eat()
            right = parse_and()
            left = 1 if (_is_truthy(left) or _is_truthy(right)) else 0
        return left
    
    def parse_and() -> Any:
        """Parse AND expressions."""
        left = parse_cmp()
        while peek()[0] == TokenType.KW.value and peek()[1] == "and":
            eat()
            right = parse_cmp()
            left = 1 if (_is_truthy(left) and _is_truthy(right)) else 0
        return left
    
    def parse_cmp() -> Any:
        """Parse comparison expressions."""
        left = parse_add()
        if peek()[0] == TokenType.OP.value and peek()[1] in ("==", "<", ">", "<=", ">="):
            op = eat()[1]
            right = parse_add()
            comparisons = {
                "==": lambda l, r: 1 if l == r else 0,
                "<": lambda l, r: 1 if l < r else 0,
                ">": lambda l, r: 1 if l > r else 0,
                "<=": lambda l, r: 1 if l <= r else 0,
                ">=": lambda l, r: 1 if l >= r else 0,
            }
            return comparisons[op](left, right)
        return left
    
    def parse_add() -> Any:
        """Parse addition and subtraction."""
        left = parse_mul()
        while peek()[0] == TokenType.OP.value and peek()[1] in ("+", "-"):
            op = eat()[1]
            right = parse_mul()
            if op == "+":
                left = str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right
            else:
                left = left - right
        return left
    
    def parse_mul() -> Any:
        """Parse multiplication and division."""
        left = parse_unary()
        while peek()[0] == TokenType.OP.value and peek()[1] in ("*", "/"):
            op = eat()[1]
            right = parse_unary()
            left = left * right if op == "*" else left / right
        return left
    
    def parse_unary() -> Any:
        """Parse unary expressions."""
        if peek()[0] == TokenType.OP.value and peek()[1] == "-":
            eat()
            return -parse_unary()
        if peek()[0] == TokenType.KW.value and peek()[1] == "not":
            eat()
            v = parse_unary()
            return 0 if _is_truthy(v) else 1
        return parse_atom()
    
    def parse_atom() -> Any:
        """Parse atomic expressions (literals, variables, function calls, parentheses)."""
        t = eat()
        
        if t[0] == TokenType.NUM.value:
            return t[1]
        if t[0] == TokenType.STR.value:
            return t[1]
        if t[0] == TokenType.KW.value:
            return 1 if t[1] == "true" else 0
        
        if t[0] == TokenType.ID.value:
            if peek()[0] == TokenType.OP.value and peek()[1] == "(":
                return _parse_call(t[1], eat, peek, expect, parse_expr)
            if t[1] not in env:
                raise NameError(f"undefined {t[1]}")
            return env[t[1]]
        
        if t[0] == TokenType.OP.value and t[1] == "(":
            v = parse_expr()
            expect(TokenType.OP.value, ")")
            return v
        
        raise SyntaxError(f"unexpected {t}")
    
    def _parse_call(fn_name: str, eat: Callable, peek: Callable, expect: Callable, parse_expr: Callable) -> Any:
        """Parse a function call."""
        eat()  # consume (
        args = []
        if not (peek()[0] == TokenType.OP.value and peek()[1] == ")"):
            args.append(parse_expr())
            while peek()[0] == TokenType.OP.value and peek()[1] == ",":
                eat()
                args.append(parse_expr())
        expect(TokenType.OP.value, ")")
        
        if fn_name not in BUILTIN_FUNCTIONS:
            raise NameError(f"unknown fn {fn_name}")
        return BUILTIN_FUNCTIONS[fn_name](*args)
    
    def _parse_if(eat: Callable, peek: Callable, expect: Callable, parse_expr: Callable) -> Any:
        """Parse an if-then-else expression."""
        eat()  # consume 'if'
        cond = parse_expr()
        expect(TokenType.KW.value, "then")
        a = parse_expr()
        expect(TokenType.KW.value, "else")
        b = parse_expr()
        return a if _is_truthy(cond) else b
    
    def _parse_let(eat: Callable, peek: Callable, expect: Callable, parse_expr: Callable, env: Dict) -> Any:
        """Parse a let binding."""
        eat()  # consume 'let'
        name = expect(TokenType.ID.value)[1]
        expect(TokenType.OP.value, "=")
        val = parse_expr()
        expect(TokenType.KW.value, "in")
        
        old = env.get(name)
        had = name in env
        env[name] = val
        try:
            return parse_expr()
        finally:
            if had:
                env[name] = old
            else:
                del env[name]
    
    return parse_expr()
```

Main improvements:
- Extracted token parsing into dedicated functions (_parse_operator, _parse_number, _parse_identifier, _parse_string)
- Created enums and constants for token types, keywords, operators, and builtin functions
- Extracted complex parsing logic (_parse_if, _parse_let, _parse_call) into separate functions
- Simplified conditional logic using dictionaries and lambdas where appropriate
- Added type hints for clarity
- Improved error messages with f-strings
- Extracted _is_truthy helper function for consistency
- Reduced code duplication and improved testability
