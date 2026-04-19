## Example 1
A=1
B=5
C=6
D=2
E=4
F=3
note: A is best because it pre-resolves coupon once and has cleanest helper signatures; C has awkward None-guard in apply_member_discount; B/C/E pass too many args through calculate_item_price.

## Example 2
A=5
B=2
C=4
D=3
E=1
F=6
note: E is best for full decomposition plus real sha256 hashing; F has a fragile None comparison in login (no explicit None check) and useless _get_cursor wrapper.

## Example 3
A=1
B=3
C=2
D=4
E=5
F=6
note: D/E/F silently drop sanitization of field values (correctness regression); A/B/C preserve it correctly; A uses DictWriter for cleaner output.

## Example 4
A=3
B=4
C=6
D=1
E=2
F=5
note: D is most complete — Address with tax_rate, LineItem, and format_address compat shim; C's Decimal type is over-engineering that changes the interface.

## Example 5
A=5
B=4
C=1
D=3
E=2
F=6
note: F changes boolean defaults (semantic bug); A over-engineers with four nested dataclasses; C is the best-balanced flat dataclass approach.

## Example 6
A=4
B=1
C=6
D=2
E=5
F=3
note: B uses a typed CarrierConfig dataclass with clear field names; C over-engineers with an apply_international_before_express flag that adds complexity without real benefit.

## Example 7
A=5
B=3
C=6
D=2
E=4
F=1
note: F is best — from_hm factory with validation, properties for hhmm strings, and batch participant validation; C over-engineers with a Meeting wrapper class.

## Example 8
A=6
B=4
C=1
D=2
E=5
F=3
note: C and D are nearly identical and cleanest — threshold list with descriptive enum values; A's BMIThreshold dataclass is pointless indirection.

## Example 9
A=1
B=4
C=5
D=3
E=2
F=6
note: F introduces semantic bugs via its transition table (REVIEWED can go to SUBMITTED, archive transitions don't match original); A is cleanest and correct.

## Example 10
A=4
B=2
C=5
D=6
E=3
F=1
note: F is cleanest — proper logging, config dataclass, set_retries method, no instance log list; D adds verbose property wrappers without benefit.

## Example 11
A=6
B=4
C=1
D=2
E=11
F=5
G=7
H=9
I=10
J=8
K=3
L=12
note: C ranks first for its clean (result, error) tuple returns, proper dataclasses with encapsulated add(), precise disc is None check, and well-named _read_csv_file helper; L ranks last due to a correctness bug in the multi-file merge that silently discards tax amounts.

## Example 12
A=4
B=2
C=5
D=10
E=11
F=12
G=1
H=7
I=9
J=6
K=8
L=3
note: G ranks first for combining a clean _Parser class with correct builtin dispatch (*args), good method decomposition, and clear helpers; F ranks last for a variable-shadowing correctness bug in the let branch on top of a changed builtin calling convention.

## Example 13
A=4
B=1
C=8
D=5
E=11
F=6
G=2
H=9
I=7
J=12
K=3
L=10
note: B ranks first for combining the cleanest decomposition (separate _price_event, COMMITMENT_DISCOUNTS table, correct defaults) while J ranks last for a truthy if inv: guard that silently drops zero-total invoices and an inconsistent mix of raw dicts and dataclasses.

## Example 14
A=7
B=4
C=8
D=10
E=1
F=9
G=12
H=2
I=11
J=6
K=5
L=3
note: E ranks first for combining the most semantic response helpers (ok/created/no_content), guard helpers for both auth and admin, expanded readable variable names, and the most thorough type annotations; G ranks last because it uses .replace("Bearer ", "") in two places.
