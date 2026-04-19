```python
import re
from enum import Enum, auto

class TokenType(Enum):
    OP = auto()
    NUM = auto()
    STR = auto()
    ID = auto()
    KW = auto()
    EOF = auto()

KEYWORDS = {"if", "then", "else", "let", "in", "and", "or", "not", "true", "false"}
OPERATOR_CHARS = "+-*/()<>=,;"
TWO_CHAR_OPS = {"==", "<=", ">="}

def tokenize(src):
    tokens = []
    i = 0
    while i < len(src):
        c = src[i]
        
        # Skip whitespace
        if c.isspace():
            i += 1
            continue
        
        # Handle operators
        if c in OPERATOR_CHARS:
            # Check for two-character operators
            if i + 1 < len(src) and c + src[i+1] in TWO_CHAR_OPS:
                tokens.append((TokenType.OP, c + src[i+1]))
                i += 2
                continue
            tokens.append((TokenType.OP, c))
            i += 1
            continue
        
        # Handle numbers
        if c.isdigit():
            j = i
            while j < len(src) and (src[j].isdigit() or src[j] == "."):
                j += 1
            num_str = src[i:j]
            num_val = float(num_str) if "." in num_str else int(num_str)
            tokens.append((TokenType.NUM, num_val))
            i = j
            continue
        
        # Handle identifiers and keywords
        if c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            token_type = TokenType.KW if word in KEYWORDS else TokenType.ID
            tokens.append((token_type, word))
            i = j
            continue
        
        # Handle strings
        if c == '"':
            j = i + 1
            while j < len(src) and src[j] != '"':
                j += 1
            tokens.append((TokenType.STR, src[i+1:j]))
            i = j + 1
            continue
        
        raise SyntaxError(f"bad char {c}")
    
    tokens.append((TokenType.EOF, None))
    return tokens

class Parser:
    def __init__(self, tokens, env=None):
        self.tokens = tokens
        self.pos = 0
        self.env = env if env is not None else {}
    
    def peek(self):
        return self.tokens[self.pos]
    
    def eat(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token
    
    def check(self, token_type, value=None):
        t = self.peek()
        if value is None:
            return t[0] == token_type
        return t[0] == token_type and t[1] == value
    
    def expect(self, token_type, value=None):
        if not self.check(token_type, value):
            raise SyntaxError(f"expected {token_type} {value}")
        return self.eat()
    
    def parse(self):
        return self.parse_expr()
    
    def parse_expr(self):
        if self.check(TokenType.KW, "if"):
            return self._parse_if_expr()
        if self.check(TokenType.KW, "let"):
            return self._parse_let_expr()
        return self.parse_or()
    
    def _parse_if_expr(self):
        self.eat()  # consume 'if'
        cond = self.parse_expr()
        self.expect(TokenType.KW, "then")
        a = self.parse_expr()
        self.expect(TokenType.KW, "else")
        b = self.parse_expr()
        return a if self._truthy(cond) else b
    
    def _parse_let_expr(self):
        self.eat()  # consume 'let'
        name = self.expect(TokenType.ID)[1]
        self.expect(TokenType.OP, "=")
        val = self.parse_expr()
        self.expect(TokenType.KW, "in")
        
        old = self.env.get(name)
        had = name in self.env
        self.env[name] = val
        try:
            return self.parse_expr()
        finally:
            if had:
                self.env[name] = old
            else:
                del self.env[name]
    
    def parse_or(self):
        left = self.parse_and()
        while self.check(TokenType.KW, "or"):
            self.eat()
            right = self.parse_and()
            left = 1 if (self._truthy(left) or self._truthy(right)) else 0
        return left
    
    def parse_and(self):
        left = self.parse_cmp()
        while self.check(TokenType.KW, "and"):
            self.eat()
            right = self.parse_cmp()
            left = 1 if (self._truthy(left) and self._truthy(right)) else 0
        return left
    
    def parse_cmp(self):
        left = self.parse_add()
        if self.check(TokenType.OP) and self.peek()[1] in ("==", "<", ">", "<=", ">="):
            op = self.eat()[1]
            right = self.parse_add()
            return self._compare(op, left, right)
        return left
    
    def _compare(self, op, left, right):
        comparisons = {
            "==": lambda l, r: l == r,
            "<": lambda l, r: l < r,
            ">": lambda l, r: l > r,
            "<=": lambda l, r: l <= r,
            ">=": lambda l, r: l >= r,
        }
        return 1 if comparisons[op](left, right) else 0
    
    def parse_add(self):
        left = self.parse_mul()
        while self.check(TokenType.OP) and self.peek()[1] in ("+", "-"):
            op = self.eat()[1]
            right = self.parse_mul()
            if op == "+":
                left = str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right
            else:
                left = left - right
        return left
    
    def parse_mul(self):
        left = self.parse_unary()
        while self.check(TokenType.OP) and self.peek()[1] in ("*", "/"):
            op = self.eat()[1]
            right = self.parse_unary()
            left = left * right if op == "*" else left / right
        return left
    
    def parse_unary(self):
        if self.check(TokenType.OP, "-"):
            self.eat()
            return -self.parse_unary()
        if self.check(TokenType.KW, "not"):
            self.eat()
            v = self.parse_unary()
            return 0 if self._truthy(v) else 1
        return self.parse_atom()
    
    def parse_atom(self):
        t = self.eat()
        
        if t[0] == TokenType.NUM:
            return t[1]
        if t[0] == TokenType.STR:
            return t[1]
        if t[0] == TokenType.KW:
            return 1 if t[1] == "true" else 0
        if t[0] == TokenType.ID:
            return self._parse_id_or_call(t[1])
        if t[0] == TokenType.OP and t[1] == "(":
            v = self.parse_expr()
            self.expect(TokenType.OP, ")")
            return v
        
        raise SyntaxError(f"unexpected {t}")
    
    def _parse_id_or_call(self, name):
        if self.check(TokenType.OP, "("):
            return self._parse_function_call(name)
        if name not in self.env:
            raise NameError(f"undefined {name}")
        return self.env[name]
    
    def _parse_function_call(self, name):
        self.eat()  # consume '('
        args = []
        
        if not self.check(TokenType.OP, ")"):
            args.append(self.parse_expr())
            while self.check(TokenType.OP, ","):
                self.eat()
                args.append(self.parse_expr())
        
        self.expect(TokenType.OP, ")")
        
        functions = {
            "min": min,
            "max": max,
            "abs": lambda x: abs(x[0]) if x else 0,
            "len": lambda x: len(x[0]) if x else 0,
        }
        
        if name not in functions:
            raise NameError(f"unknown fn {name}")
        
        return functions[name](args)
    
    @staticmethod
    def _truthy(v):
        return v not in (0, 0.0, "", None, False)

def evaluate(src, env=None):
    tokens = tokenize(src)
    parser = Parser(tokens, env)
    return parser.parse()
```

Refactoring notes:
- Introduced `TokenType` enum for type safety and clarity
- Extracted constants (`KEYWORDS`, `OPERATOR_CHARS`, `TWO_CHAR_OPS`) to reduce magic strings
- Created `Parser` class to encapsulate parsing state instead of using nested functions with `pos` list
- Consolidated repetitive token checking with a `check()` helper method
- Moved comparison logic to a `_compare()` method to reduce inline conditionals
- Extracted function call parsing to `_parse_function_call()` for clarity
- Simplified `_truthy()` using set membership
- Used dictionary dispatch for built-in functions
- Improved error messages with f-strings
- Better separation of concerns: tokenizer returns typed tokens, parser handles all parsing logic
