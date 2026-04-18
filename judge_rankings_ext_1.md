## Example 11
A=5
B=11
C=1
D=3
E=9
F=4
G=7
H=8
I=6
J=10
K=2
L=12
note: C ranks first for combining fully-typed dataclasses, an encapsulated add() method, clean (result, error) return pairs, and pure helper functions with no mixed concerns; L ranks last for a correctness bug in the cross-file accumulator merge (tax is passed as 0 during region combining) and for using raw dicts inside the dataclass instead of a SkuBucket.

## Example 12
A=5
B=1
C=4
D=10
E=12
F=11
G=2
H=8
I=9
J=3
K=6
L=7
note: B ranks first for combining a proper _Parser class, clean method decomposition (_parse_if/_parse_let/_call_builtin factored), module-level dispatch tables, and a regex tokenizer with correct *args call convention; E ranks last because despite using a _Parser class it undercuts itself with a redundant identity-dict for compound ops, verbose t[0]/t[1] guards where tuple equality would do, and _CMP_OPS oddly stored as a class attribute.

## Example 13
A=5
B=2
C=11
D=3
E=9
F=4
G=6
H=7
I=8
J=10
K=1
L=12
note: K ranks first for combining all the right abstractions (dispatch table, commitment-discount table, dataclasses with as_dict() for compatibility) with no design flaws, while L ranks last for storing usage rules as a list of tuples that must be rebuilt into a dict on every call — an antipattern that defeats the purpose of a dispatch table.

## Example 14
A=8
B=6
C=4
D=9
E=1
F=11
G=12
H=2
I=10
J=7
K=5
L=3
note: E ranks first for introducing the most extensible abstractions (semantic response constructors ok/created/no_content, both _require_auth and _require_admin guards, and parametric type annotations), while G ranks last for using .replace("Bearer ", "") instead of removeprefix in two places — a correctness regression compared to every other variant.
