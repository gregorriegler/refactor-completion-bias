## Example 1
A=2
B=4
C=6
D=1
E=5
F=3
note: D edges out A by also extracting apply_bulk_discount; C's awkward `if rate is not None` pattern when .get(..., 1.0) would suffice lands it last.

## Example 2
A=3
B=1
C=5
D=2
E=4
F=6
note: B and D give the fullest SRP decomposition; C and E silently change the hash algorithm (semantic break); F has a subtle None-comparison bug in login.

## Example 3
A=3
B=2
C=1
D=4
E=5
F=6
note: D/E/F are code-identical and silently drop explicit sanitization (trusting csv quoting for newlines changes output semantics); C and B preserve sanitization with csv.writer tuples, C slightly cleaner layout.

## Example 4
A=3
B=2
C=5
D=1
E=4
F=6
note: D and B extract both Address and LineItem; D's multiline f-string in __str__ is cleaner; C introduces Decimal without justification; F uses format() instead of __str__ and converts properties to methods without clear benefit.

## Example 5
A=1
B=3
C=2
D=5
E=4
F=6
note: A's three-level config hierarchy (Metadata/Sections/Style) best separates concerns; F silently changes boolean defaults (include_summary/charts/tables True instead of False), breaking existing callers.

## Example 6
A=4
B=3
C=1
D=2
E=5
F=6
note: C is the only variant that correctly preserves the per-carrier ordering of express vs international surcharge (DHL adds international before multiplying express; fedex multiplies express before adding international); all others apply international then express uniformly, which is wrong for fedex.

## Example 7
A=5
B=3
C=6
D=1
E=4
F=2
note: D and F both use frozen TimeSlot with from_hm classmethod for validated construction and batch email reporting; C's Meeting wrapper class adds indirection without meaningful benefit.

## Example 8
A=5
B=4
C=1
D=3
E=6
F=2
note: C and F use descriptive enum names and a threshold list that eliminates the if-chain; E's partial RECOMMENDATIONS dict (handling only Normal and Obese) mixed with an if-chain is inconsistently structured; A's BMIThreshold dataclass adds abstraction for no gain.

## Example 9
A=1
B=4
C=5
D=3
E=2
F=6
note: A is the cleanest correct refactor; F's _VALID_TRANSITIONS table restricts archive() to fewer states than the original allows (semantic change); C adds REVIEWED->SUBMITTED back-transition not present in the original.

## Example 10
A=3
B=2
C=6
D=5
E=4
F=1
note: F is the clearest: logging module, config property, set_retries method, no property-setter complexity; C and D retain the log-list pattern which is inferior to Python's logging infrastructure.
