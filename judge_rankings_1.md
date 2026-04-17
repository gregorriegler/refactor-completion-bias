## Example 1
A=1
B=5
C=6
D=3
E=4
F=2
note: A best for type hints + named constants + clean private helpers; C worst for awkward None-check in apply_member_discount

## Example 2
A=3
B=4
C=1
D=5
E=2
F=6
note: C best for dependency injection + real hashing + regex validation; F worst for keeping monolith and potential None comparison issue in login

## Example 3
A=5
B=3
C=2
D=1
E=6
F=4
note: D/C best for clean csv.writer + separate rows list + no extraneous complexity; E worst for unused io import and unnecessary row_builder callback

## Example 4
A=3
B=6
C=1
D=2
E=4
F=5
note: C/D best for __str__ on Address + LineItem dataclass + properties throughout; B worst for mixed property/method inconsistency between Address and Invoice

## Example 5
A=5
B=1
C=4
D=2
E=3
F=6
note: B best for Literal type hint, sensible defaults, single clean config object; F worst for changed defaults on include_ flags which alters semantics

## Example 6
A=1
B=6
C=5
D=4
E=2
F=3
note: A best for clean dict config with no over-engineering; B worst for express_before_international flag that over-engineers ordering concern; C reintroduces carrier-specific branching

## Example 7
A=5
B=3
C=6
D=1
E=4
F=2
note: D best for elegant from_hm factory + start_label/end_label methods; F slightly over-engineers with properties but still clean; C adds __str__ to TimeSlot that is unused in schedule_meeting

## Example 8
A=5
B=2
C=3
D=1
E=6
F=4
note: D best for descriptive enum values + threshold list pattern without over-engineering; E worst for inconsistent BmiCategory naming and awkward partial RECOMMENDATIONS dict

## Example 9
A=1
B=6
C=5
D=3
E=2
F=4
note: A best for clean simple state enum without spurious transition table; B worst for _TRANSITIONS dict that is barely used and inconsistently applied

## Example 10
A=4
B=2
C=1
D=6
E=5
F=3
note: C best for FetcherConfig + set_retries method + descriptive log messages; D worst for keeping list-based logging instead of switching to proper logging module
