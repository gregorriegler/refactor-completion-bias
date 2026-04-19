## Example 1
A=2
B=4
C=6
D=1
E=5
F=3
note: D best — resolves coupon once outside loop, extracts apply_bulk_discount, clean pipeline; C has awkward None-guard in apply_member_discount; B/E/F pass too many params through calculate_item_price

## Example 2
A=3
B=1
C=5
D=2
E=6
F=4
note: B/D best — proper separation into Repository/EmailSender/AuditLogger; C and E silently change hash function (semantics change); F has trivial _get_cursor wrapper and login None-safety relies on Python truthy comparison

## Example 3
A=4
B=5
C=6
D=1
E=2
F=3
note: D/E/F use csv.DictWriter correctly (csv module handles quoting natively, making manual sanitization redundant); A/B/C do unnecessary manual sanitization alongside csv; D, E, F are nearly identical, ranked by tie-break on minor style

## Example 4
A=1
B=3
C=6
D=2
E=4
F=5
note: A cleanest — Address with __str__, tax_rate on Invoice via lookup, no redundant format_address; B good but putting tax_rate on Address conflates concerns; C over-engineers with Decimal (semantic change); F breaks str protocol by using .format() instead of __str__

## Example 5
A=1
B=2
C=5
D=3
E=4
F=6
note: A best — groups params into ReportMetadata/Sections/Style sub-dataclasses, clear domain decomposition; F changes default boolean values (semantic change); C/D/E all use flat ReportConfig with SECTION list, ranked by clarity

## Example 6
A=4
B=2
C=1
D=3
E=5
F=6
note: C is the only variant that correctly preserves FedEx ordering (express applied before international surcharge, matching original); all others apply international before express for FedEx, producing different results; B/D use cleaner typed dataclass over plain dict

## Example 7
A=5
B=3
C=6
D=2
E=4
F=1
note: F best — frozen TimeSlot, from_hm factory with validation, clean properties start_hhmm/end_hhmm, collects all invalid emails; C over-engineers with a Meeting wrapper class that adds indirection without real benefit; A uses mutable dataclass

## Example 8
A=5
B=3
C=1
D=4
E=6
F=2
note: C/F cleanest — threshold list pattern eliminates repeated if-chain, full-word enum values are more readable; A over-engineers with BMIThreshold dataclass; E over-engineers further with partial RECOMMENDATIONS dict (inconsistent handling of age-dependent cases); D identical to C but uses == instead of is for enum comparison

## Example 9
A=1
B=4
C=5
D=2
E=3
F=6
note: A cleanest — straightforward enum replacement, no excess machinery; F has semantic differences (allows archiving from REVIEWED/APPROVED, not in original); C allows REVIEWED->SUBMITTED re-submission (also not in original); B's archive uses _TRANSITIONS dict in a fragile way

## Example 10
A=2
B=1
C=5
D=4
E=6
F=3
note: B cleanest — logging module, FetcherConfig dataclass, set_retries method matches original API; E renames class to FetchClient (API breakage); C/D preserve instance log list (closer to original but log list is a design smell worth removing); A uses property setter for retries (elegant but changes calling convention)

## Example 11
A=3
B=6
C=1
D=4
E=9
F=5
G=7
H=8
I=11
J=10
K=2
L=12
note: C ranks first for its clean (value, err) tuple parse interface, typed constants, and graceful LATAM handling via None-check, while L ranks last for a correctness bug in the multi-file accumulator merge that silently undercounts tax.

## Example 12
A=1
B=4
C=6
D=9
E=11
F=10
G=3
H=8
I=12
J=7
K=5
L=2
note: A ranks first for combining a single compiled regex tokenizer with correct module-level constants, proper helper extraction, and no calling-convention bugs, while I ranks last for the awkward pre-computing-all-comparisons pattern in parse_cmp and the unused COMPOUND_OPS indirection.

## Example 13
A=6
B=1
C=8
D=3
E=12
F=7
G=5
H=4
I=9
J=11
K=2
L=10
note: B ranks first for combining a clean class-level USAGE_CONFIG dispatch table, a dedicated _price_event helper, a COMMITMENT_DISCOUNTS table, and usage-log pre-filtering; E ranks last because it mixes @dataclass engine with raw dict lines/invoices and risks a KeyError on commitment_months.

## Example 14
A=5
B=3
C=8
D=11
E=1
F=10
G=12
H=4
I=9
J=2
K=7
L=6
note: E ranks first for its granular response helpers, descriptive errors, _require_auth/_require_admin guards, and comprehensive type annotations; G ranks last for retaining .replace("Bearer ", "") instead of removeprefix.
