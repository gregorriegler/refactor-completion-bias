# Example 12: Mini expression interpreter (deep nesting, string dispatch)

```python
def tokenize(src):
    tokens = []
    i = 0
    while i < len(src):
        c = src[i]
        if c == " " or c == "\t" or c == "\n":
            i += 1
            continue
        if c in "+-*/()<>=,;":
            if c == "=" and i + 1 < len(src) and src[i+1] == "=":
                tokens.append(("op", "=="))
                i += 2
                continue
            if c == "<" and i + 1 < len(src) and src[i+1] == "=":
                tokens.append(("op", "<="))
                i += 2
                continue
            if c == ">" and i + 1 < len(src) and src[i+1] == "=":
                tokens.append(("op", ">="))
                i += 2
                continue
            tokens.append(("op", c))
            i += 1
            continue
        if c.isdigit():
            j = i
            while j < len(src) and (src[j].isdigit() or src[j] == "."):
                j += 1
            num = src[i:j]
            tokens.append(("num", float(num) if "." in num else int(num)))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            if word in ("if", "then", "else", "let", "in", "and", "or", "not", "true", "false"):
                tokens.append(("kw", word))
            else:
                tokens.append(("id", word))
            i = j
            continue
        if c == '"':
            j = i + 1
            while j < len(src) and src[j] != '"':
                j += 1
            tokens.append(("str", src[i+1:j]))
            i = j + 1
            continue
        raise SyntaxError("bad char " + c)
    tokens.append(("eof", None))
    return tokens

def evaluate(src, env=None):
    if env is None:
        env = {}
    tokens = tokenize(src)
    pos = [0]
    def peek():
        return tokens[pos[0]]
    def eat():
        t = tokens[pos[0]]
        pos[0] += 1
        return t
    def parse_expr():
        if peek()[0] == "kw" and peek()[1] == "if":
            eat()
            cond = parse_expr()
            if not (peek()[0] == "kw" and peek()[1] == "then"):
                raise SyntaxError("expected then")
            eat()
            a = parse_expr()
            if not (peek()[0] == "kw" and peek()[1] == "else"):
                raise SyntaxError("expected else")
            eat()
            b = parse_expr()
            return cond if False else (a if _truthy(cond) else b)
        if peek()[0] == "kw" and peek()[1] == "let":
            eat()
            if peek()[0] != "id":
                raise SyntaxError("expected id")
            name = eat()[1]
            if not (peek()[0] == "op" and peek()[1] == "="):
                raise SyntaxError("expected =")
            eat()
            val = parse_expr()
            if not (peek()[0] == "kw" and peek()[1] == "in"):
                raise SyntaxError("expected in")
            eat()
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
        return parse_or()
    def parse_or():
        left = parse_and()
        while peek()[0] == "kw" and peek()[1] == "or":
            eat()
            right = parse_and()
            left = 1 if (_truthy(left) or _truthy(right)) else 0
        return left
    def parse_and():
        left = parse_cmp()
        while peek()[0] == "kw" and peek()[1] == "and":
            eat()
            right = parse_cmp()
            left = 1 if (_truthy(left) and _truthy(right)) else 0
        return left
    def parse_cmp():
        left = parse_add()
        if peek()[0] == "op" and peek()[1] in ("==", "<", ">", "<=", ">="):
            op = eat()[1]
            right = parse_add()
            if op == "==": return 1 if left == right else 0
            if op == "<":  return 1 if left < right else 0
            if op == ">":  return 1 if left > right else 0
            if op == "<=": return 1 if left <= right else 0
            if op == ">=": return 1 if left >= right else 0
        return left
    def parse_add():
        left = parse_mul()
        while peek()[0] == "op" and peek()[1] in ("+", "-"):
            op = eat()[1]
            right = parse_mul()
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    left = str(left) + str(right)
                else:
                    left = left + right
            else:
                left = left - right
        return left
    def parse_mul():
        left = parse_unary()
        while peek()[0] == "op" and peek()[1] in ("*", "/"):
            op = eat()[1]
            right = parse_unary()
            if op == "*":
                left = left * right
            else:
                left = left / right
        return left
    def parse_unary():
        if peek()[0] == "op" and peek()[1] == "-":
            eat()
            return -parse_unary()
        if peek()[0] == "kw" and peek()[1] == "not":
            eat()
            v = parse_unary()
            return 0 if _truthy(v) else 1
        return parse_atom()
    def parse_atom():
        t = eat()
        if t[0] == "num": return t[1]
        if t[0] == "str": return t[1]
        if t[0] == "kw" and t[1] == "true": return 1
        if t[0] == "kw" and t[1] == "false": return 0
        if t[0] == "id":
            if peek()[0] == "op" and peek()[1] == "(":
                eat()
                args = []
                if not (peek()[0] == "op" and peek()[1] == ")"):
                    args.append(parse_expr())
                    while peek()[0] == "op" and peek()[1] == ",":
                        eat()
                        args.append(parse_expr())
                if not (peek()[0] == "op" and peek()[1] == ")"):
                    raise SyntaxError("expected )")
                eat()
                if t[1] == "min": return min(args)
                if t[1] == "max": return max(args)
                if t[1] == "abs": return abs(args[0])
                if t[1] == "len": return len(args[0])
                raise NameError("unknown fn " + t[1])
            if t[1] not in env:
                raise NameError("undefined " + t[1])
            return env[t[1]]
        if t[0] == "op" and t[1] == "(":
            v = parse_expr()
            if not (peek()[0] == "op" and peek()[1] == ")"):
                raise SyntaxError("expected )")
            eat()
            return v
        raise SyntaxError("unexpected " + str(t))
    def _truthy(v):
        if v == 0 or v == 0.0 or v == "" or v is None or v is False:
            return False
        return True
    return parse_expr()
```
