## Example 11
A=3
B=9
C=1
D=2
E=10
F=5
G=6
H=7
I=11
J=8
K=4
L=12
note: C ranks first for combining clean (result, error) tuple returns, properly-used RegionData.add(), and typed dataclasses into the most extensible and testable structure; L ranks last due to a correctness bug in its cross-file accumulator merge that silently zeroes out tax contributions.

## Example 12
A=5
B=1
C=4
D=11
E=8
F=10
G=2
H=9
I=12
J=3
K=6
L=7
note: B tops for combining a proper _Parser class, four distinct helper predicates, factored sub-rules, correct *args builtin dispatch, and full type annotations; I bottoms for its eager-evaluation comparison dict (computes all five comparisons before selecting one), a COMPOUND_OPS constant that is defined but never used, and retaining the closure/pos=[0] pattern with no structural improvement.

## Example 13
A=5
B=1
C=7
D=2
E=8
F=6
G=3
H=11
I=10
J=9
K=4
L=12
note: B ranks first for combining typed dataclasses, a compact USAGE_CONFIG dispatch table, a COMMITMENT_DISCOUNTS tier list, and a clean _price_event split — all correctness-preserving; L ranks last because its USAGE_RULES list requires rebuilding a dict on every invocation and its commitment discount still embeds magic literals inline.

## Example 14
A=7
B=6
C=9
D=10
E=1
F=11
G=12
H=3
I=5
J=8
K=4
L=2
note: E ranks first for introducing semantic HTTP helpers (ok/created/no_content), dual auth-guard functions (_require_auth/_require_admin), and the richest type annotations — the most extensible structure overall; G ranks last for using .replace("Bearer ", "") instead of .removeprefix in two places, introducing a correctness defect that every other variant explicitly avoided.
