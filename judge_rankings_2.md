## Example 1
A=1
B=5
C=6
D=3
E=4
F=2

note: A is cleanest with typed helpers and constants; C has awkward membership-discount fallback logic; D/F precompute discount once (semantically fine); B/E pack too much into price_item.

## Example 2
A=1
B=4
C=3
D=5
E=2
F=6

note: F has a bug — login compares stored (possibly None) to hashed without None guard; A upgrades to sha256 and uses stdlib logging cleanly; E similar to A but keeps interface simpler.

## Example 3
A=4
B=3
C=2
D=1
E=6
F=5

note: D and C are nearly identical and best; E introduces an unnecessary row_builder callback abstraction; F and A use DictWriter which is heavier than needed here.

## Example 4
A=3
B=5
C=1
D=2
E=4
F=6

note: C and D are essentially identical — full decomposition with Address, LineItem, and Invoice all using properties; B oddly puts tax_rate on Address; F uses plain methods instead of properties losing expressiveness.

## Example 5
A=2
B=1
C=5
D=3
E=4
F=6

note: F changes include_charts and include_tables defaults to True, altering semantics; B has sensible defaults and one clean config object; A's three-way split is nice but creates more call-site complexity.

## Example 6
A=4
B=5
C=6
D=1
E=2
F=3

note: C re-introduces a carrier-name check defeating the refactor goal; B over-engineers an express_before_international flag; D uses a clean typed dataclass with uniform application order (correct for all carriers).

## Example 7
A=5
B=3
C=6
D=2
E=4
F=1

note: F is cleanest — frozen dataclass, from_hm factory with validation, and hhmm properties keep schedule_meeting very tight; A lacks frozen=True; C has slightly redundant end-time computation in schedule_meeting.

## Example 8
A=5
B=1
C=4
D=2
E=6
F=3

note: B is simplest and correct — enum with full names, plain if-chain with inline thresholds, is-comparison; E awkwardly splits RECOMMENDATIONS into a dict for some categories but not others; A wraps thresholds in a dataclass unnecessarily.

## Example 9
A=4
B=6
C=5
D=3
E=1
F=2

note: E uses `is` comparison for enum identity (idiomatic Python), full transition table plus sensible special-case for review; B defines _TRANSITIONS dict but uses it awkwardly for archive; A is clean but lacks transition table.

## Example 10
A=4
B=1
C=2
D=6
E=5
F=3

note: D keeps a list-based log instead of using Python's logging module, missing the point of the refactor; B and C are nearly identical and best; E skips the config dataclass which reduces composability.
