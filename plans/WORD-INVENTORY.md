# Word Inventory: forthic-ts vs forthic-py (2026-07-12)

**STATUS: WORKING PLAN — word batches all TODO. Phase 1 (correctness
tier) landed first and already resolved several items flagged below:
ANY empty-items2 → false; >BOOL/OR/AND/NOT/XOR/NAND/SELECT truthiness via
the new `forthic.utils.is_truthy`; ==/!=/IN/ANY/ALL via `values_equal`
(bools ≠ numbers, int/float unify, datetime tz-sensitive, structural
records); the six array_module key-sorting sites (NTH, LAST, SLICE, TAKE,
DROP, UNPACK) — TAKE/DROP now return records for records; SLICE 10M span
guard; DIFFERENCE/INTERSECTION rebuilt on the ts set_op contract; >STR
JS semantics; >JSON compact; crash-proof error formatter;
IntentionalStop unwrapped; reset() completeness. Correction to this
inventory: RELABEL's sorted() (array arm) MATCHES ts classic RELABEL —
not a bug, keep it.**

Full audit of both standard libraries, extracted by runtime enumeration of
registered words on both sides (StandardInterpreter → registered modules →
word lists), not by grepping decorators. ts canonical = **169 unique words**
(8 modules: core 33, array 39, record 15, string 28, math 20, boolean 15,
json 2, datetime 17) + **34 classic words** = 203 names — matches the rs
inventory's counts exactly. py = **141 unique words**. Missing from py
(set-verified): **73 canonical names** = 64 words to implement + 9 that
exist under wrong (underscore) names; a 65th implementation is core DROP,
whose NAME py already has but bound to the wrong meaning (array skip-n).
py registers **all 34 ts classic words** (modulo underscore spellings).
Both runtimes resolve bare-name collisions
last-registration-wins. ts's fs_module (host interop) excluded; py's
pandas_module.py is the py analog — non-portable host interop, excluded
from the portable core, document as such.

Registration mechanism note (audit item 8 resolved): **all 8 py modules use
the same @ForthicWord/@ForthicDirectWord decorators** — record_module.py
just imports `ForthicWord as WordDecorator`, which is why a grep for
`@ForthicWord` found nothing there. The real record-module gap is coverage:
it registers only 10 words, 5 of them classic/never-port. No bare words are
registered at interpreter.py/module.py level beyond literals and structural
tokens (StartModule/EndModule/EndArray/PushValue).

## CRITICAL: same-name-different-meaning collisions (fix before porting)

Every row verified against actual py code. py has MORE collisions than rs
did — the variable-arity pattern ts deliberately removed survives in five
py word families.

| Word | ts meaning | py meaning |
|---|---|---|
| DROP | core: pop top of stack | array: skip first n (= ts SKIP), `array_module.py:186`. `1 2 DROP` and `[1 2 3] 2 DROP` mean opposite things across runtimes. py's pop is POP (the ts CLASSIC name, `core_module.py:85`). Record arm also sorts keys and collapses to a values array. |
| CONCAT | string: ( strings[] -- str ) array-only; two-string form deliberately removed (helpful error) | `string_module.py:50`: variable arity — array on top OR two-string fallback. Same arity instability ts removed. (Only one registration though — py has no array-module CONCAT, better than rs's double registration.) |
| + and * (+ classic ADD/MULTIPLY) | math: strictly two-operand; "For arrays use SUM / PRODUCT" | `math_module.py:48,89`: array-collapse form — `[1 2 3] +` sums, `[1 2 3] *` multiplies. PRODUCT doesn't exist in py, so `*`'s array arm is currently the only product path — port PRODUCT in the same change. |
| MAX / MIN | math: array-only; null elements skipped; null on empty/all-null | `math_module.py:219,237`: two-operand OR array; no null-skip (a None element raises TypeError); two-value scalar form must go. |
| OR / AND | boolean: strictly two-operand; "For arrays use ANY? / ALL?" | `boolean_module.py:73,94`: array-collapse form; element tests use raw Python truthiness (`if val:` — empty containers falsy, violating the JS-truthiness contract). Two-value form returns raw operand (`a or b`) like ts — that part is fine. |
| ANY | two-array membership: empty items2 → **false** (nothing can be in an empty set — explicit comment in ts code) | `boolean_module.py:137-144`: empty items2 → **True**. ALL matches on both sides (vacuous true for empty items2). |
| INTERPOLATE | core: `${name}` holes, names-only, READ-ONLY lookup, miss renders as null_text default "" | `core_module.py:291`: dead bare-dot `.name` grammar; lookup is get-or-create — **a typo in a template MINTS a variable** (`core_module.py:333`); null_text default "null". Full Batch 4 redesign. |
| @ | read-only fetch; undeclared string name throws UnknownVariableError, miss creates NOTHING | `core_module.py:146`: get-or-create — a miss silently creates the variable. Only ! and !@ may get-or-create. |
| LENGTH | arrays/records only; a string ERRORS pointing at STR-LENGTH | `array_module.py:58`: string → `len(str)`; other scalars → 0. |
| APPEND | arrays only (record → error pointing at JQ!); copies, never mutates the input | `array_module.py:367`: mutates the input array in place; record arm treats item as a [key, value] pair. |

Not collisions in py (unlike rs): **RANGE** is simply absent — port the ts
contract directly (inclusive; EMPTY if start > end; 10M allocation bound,
`MAX_MATERIALIZED_ELEMENTS`). **FLATTEN** (`array_module.py:912`) is already
ts-shaped — full flatten by default, depth option, records flatten to
tab-joined key paths — verify-only (see verify list).

Within-py double registration: `<` `<=` `>` `>=` are registered in BOTH
math (`math_module.py:369-383`) and boolean modules; boolean registers
later and wins. ts has them in boolean only — delete the math copies.

## Naming divergences (same semantics, wrong name)

**The underscore bug (py-specific, biggest surprise of this audit):** the
@ForthicWord decorator defaults the word name to the Python **method name**,
and 14 registrations never passed a custom name — so py serves
`GROUP_BY`, not `GROUP-BY`. Programs written against the canonical hyphen
names get UnknownWord. Rename sweep (give every one an explicit name;
consider making the decorator reject defaulted names containing `_`):

| py name (today) | canonical name | site |
|---|---|---|
| USE_MODULES | USE-MODULES | core_module.py:187 (also lacks ts options — see Batch 5) |
| BY_FIELD | BY-FIELD | array_module.py:697 |
| GROUP_BY | GROUP-BY | array_module.py:744 |
| GROUP_BY_FIELD | GROUP-BY-FIELD | array_module.py:716 |
| GROUPS_OF | GROUPS-OF | array_module.py:787 (explicit name — explicitly wrong) |
| KEY_OF | KEY-OF | array_module.py:201 |
| ZIP_WITH | ZIP-WITH | array_module.py:402 |
| RE_MATCH | RE-MATCH | string_module.py:157 |
| RE_MATCH_ALL | RE-MATCH-ALL | string_module.py:168 |
| INVERT_KEYS | INVERT-KEYS | record_module.py:157 (keep-9 classic) |
| URL_ENCODE | URL-ENCODE | string_module.py:187 (keep-9 classic) |
| URL_DECODE | URL-DECODE | string_module.py:194 (keep-9 classic) |
| RE_MATCH_GROUP | RE-MATCH-GROUP | string_module.py:176 (classic, disposition below) |
| REC_DEFAULTS | (dropping → MERGE) | record_module.py:170 |

Classic-name divergences (py name = ts canonical name): py POP = ts DROP;
py DROP = ts SKIP; py INTERPRET = ts RUN; py SELECT = ts FILTER;
py \*DEFAULT = ts DEFAULT-RUN; py IN (item-first) = ts CONTAINS?
(haystack-first, args reversed); py <DEL = ts DELETE (py's MUTATES in
place, DELETE is copy-on-write); py REC_DEFAULTS ≈ ts MERGE (REC-DEFAULTS
also overrides None/"" values — migration note); py SUBTRACT-DATES = ts
DAYS-BETWEEN (pure rename, same operand order); py >FIXED = ts
FORMAT-FIXED; py IDENTITY = ts NOP (py registers both); py <REPEAT ≈ ts
TIMES-RUN (different stack effect: <REPEAT is ( item forthic n -- ) and
pushes item+result each pass; TIMES-RUN is ( n forthic -- ), no automatic
value passing).

## ts classic words in py — dispositions

ts's classic_module.ts (34 words) exists for back-compat. **py registers
ALL 34 of them**, scattered through its canonical modules (modulo the
underscore misspellings) — py's standard library is essentially the
pre-scrub ts surface. Dispositions per the settled decisions (do not
re-litigate; tombstone-test every drop):

**Drop when the canonical sibling lands (15):**

| Classic (py site) | Canonical replacement | Batch |
|---|---|---|
| POP core_module.py:85 | DROP (core pop) | 0 |
| IDENTITY core_module.py:196 | NOP (already present) | 0 |
| ADD math_module.py:71 | + (two-operand) / SUM | 0 |
| SUBTRACT math_module.py:83 | - | 0 |
| MULTIPLY math_module.py:115 | * (two-operand) / PRODUCT | 0 |
| DIVIDE math_module.py:131 | / | 0 |
| INTERPRET core_module.py:170 | RUN | 1 |
| *DEFAULT core_module.py:221 | DEFAULT-RUN | 1 |
| IN boolean_module.py:131 | CONTAINS? (args reversed) | 1 |
| SELECT array_module.py:436 | FILTER | 2 |
| <REPEAT array_module.py:977 | TIMES-RUN (simpler semantics) | 2 |
| <DEL record_module.py:182 | DELETE (copy-on-write) | 3 |
| REC_DEFAULTS record_module.py:170 | MERGE | 3 |
| >FIXED math_module.py:295 | FORMAT-FIXED | 5 |
| SUBTRACT-DATES datetime_module.py:360 | DAYS-BETWEEN | 5 |

**Keep — the 9 no-replacement classics (py has all 9; 3 need the rename):**
XOR (boolean_module.py:119), NAND (boolean_module.py:123), RELABEL
(record_module.py:133 — its array-arm `sorted()` matches ts classic
RELABEL, keep; Phase 1 verified this),
INVERT-KEYS (record_module.py:157, rename from INVERT_KEYS), DATE>INT
(datetime_module.py:288), JSON-PRETTIFY (json_module.py:54), /R
(string_module.py:97), URL-ENCODE (string_module.py:187, rename),
URL-DECODE (string_module.py:194, rename).

**No settled disposition — py-specific, flag for owner (10):** rs never had
these, so the rs scrub never decided them. All are ts-classic with no
canonical sibling; by the same "dropping removes functionality with no
replacement" rationale the default is KEEP, but confirm:
EXPORT (core_module.py:181 — module infrastructure; ts serves it via
classic), PROFILE-START/END/TIMESTAMP/DATA (core_module.py:253-285 —
runtime tooling; py has real profiling support behind them), SHUFFLE
(array_module.py:661), ROTATE (array_module.py:334), INFINITY
(math_module.py:313), UNIFORM-RANDOM (math_module.py:317), RE-MATCH-GROUP
(string_module.py:176, rename from RE_MATCH_GROUP).

**py-only words with NO ts counterpart at all (not even classic):**
E (math_module.py:393) and PI (math_module.py:389). Not in rs either.
Owner decision: drop for parity, or propose upstream to ts. Until decided,
exclude from the portable-core count.

## Never port

- **|REC@** — removed from ts (#27, injection). **py still registers it**
  (record_module.py:94-100) and the implementation is the injection shape
  in person: it json.dumps the field into a Forthic string and runs
  `'<field> REC@' MAP`. REMOVE + tombstone test.
- **push_error** — REMOVED (Phase 2, with TRY's arrival): gone from MAP,
  FOREACH, module docs, and the word_options docstring; MAP's dead
  push_rest deleted alongside. MAP gained `.outcomes`; TRY / OK? /
  ERROR? / UNWRAP / UNWRAP-OR live in core (test_try_word.py pins the
  laws).
- **@ForthicWord None-return gap (Phase 2 finding, infrastructure
  decision needed):** the decorator only pushes non-None results, so a
  decorated word whose value is legitimately NULL pushes NOTHING —
  `NULL REVERSE`, `[] LAST`, `NULL DEFAULT`-style pass-throughs all
  strand the stack today. ts distinguishes undefined (no push) from null
  (push). Options: a NO_PUSH sentinel (decorated words that return
  nothing switch to it) or converting null-returning words to direct
  words (what UNWRAP/UNWRAP-OR do). Decide before the Batch 1/2 words
  (NULL?, FIND, MIN-BY/MAX-BY return null routinely).
- **UNDEFINED** — ts-only documented host-interop word (serializes as null
  on the wire). py never implements it; UnknownWord is the honest
  non-portability signal; portable programs use NULL.
- **MAP `interps` option** — ts has it (parallel interpreters); rs skipped
  it because rs is deliberately synchronous. py does NOT currently have it.
  py is async, so the rs excuse doesn't apply — per the plan's async
  watchpoint it is FINE to add later, but it is not required for the scrub.
  Leave absent (rs precedent) and record as backlog.
- **pandas_module.py** — py-only host interop (the ts fs_module analog).
  Never in the portable core; document as non-portable.

## Porting batches (canonical words only — every batch TODO)

**Batch 0 — collision fixes first: DONE (feat/word-batch0)**
Also landed with this batch: **stack-effect-driven push** (the decision on
the @ForthicWord None-return gap): the declared stack effect's output side
now drives the wrapper — a declared output always pushes (Python None is
Forthic NULL); `( ... -- )` never pushes, and a word that returns a value
anyway raises at execution. This made the effect strings load-bearing
(inputs already were) and fixed the `[] LAST` / `NULL REVERSE` stranding
bugs wholesale. |REC@'s removal was pulled forward from Batch 3: it could
not express itself honestly under the new contract (it declared an output
while MAP pushed for it). The decorator guard against defaulted
underscore names was NOT added — py-only host modules (pandas, the
examples module) legitimately default method names; the sweep below fixed
the standard modules instead. Original spec:
- array DROP → SKIP; add core DROP (pop); drop classic POP; drop IDENTITY
  (NOP remains). Tombstones for `1 2 DROP` old meaning.
- CONCAT array-only; two-string form rejected with a helpful message.
- `+` and `*` strictly two-operand; port PRODUCT (empty → 1; non-array →
  NULL; a NULL/non-numeric element NULLs the result — deliberate ts
  asymmetry with SUM) in the same change; drop ADD/SUBTRACT/MULTIPLY/
  DIVIDE classics.
- MAX/MIN → array-only, null elements skipped, null on empty/all-null.
- LENGTH: string operand errors toward STR-LENGTH (STR-LENGTH itself lands
  in Batch 4 — land together or sequence carefully).
- APPEND: arrays only (record → error toward JQ!); copy, don't mutate.
- Underscore rename sweep (all 14 rows of the table above; the three
  keep-9 renames and RE-MATCH-GROUP included). Consider a decorator guard
  against defaulted names containing `_`.
- Delete math's duplicate `<` `<=` `>` `>=` registrations.

**Batch 1 — control flow & predicates: DONE (feat/word-batch1)**
IF (pure value selection, is_truthy), IF-RUN (null branch no-op), WHEN,
RUN (classic INTERPRET dropped), DEFAULT-RUN (classic *DEFAULT dropped),
NULL?, EMPTY?, STRING?, NUMBER? (Infinity yes, NaN no, py bools excluded),
RECORD?, ANY? (false on empty, errors on non-array), ALL? (true on
empty), CONTAINS? (haystack-first via values_equal; classic IN dropped),
OR/AND strictly two-operand (array operand errors toward ANY?/ALL?;
two-value form keeps ts's raw-operand ||/&& selection via is_truthy).
PEEK!/STACK! verified (Phase 1 had already pinned IntentionalStop).
Spec: tests/unit/core/test_word_batch1.py. Original spec:
IF (pure value selection), IF-RUN, WHEN, RUN (drop INTERPRET), DEFAULT-RUN
(drop *DEFAULT), NULL?, EMPTY?, STRING?, NUMBER? (Infinity yes, NaN no),
RECORD?, ANY? (false on empty), ALL? (true on empty), CONTAINS?
(haystack-first; drop classic IN). PEEK!/STACK! already present (verify
IntentionalStopError behavior matches ts). Central `is_truthy` helper with
JS semantics (empty containers TRUTHY, NaN falsy, 0/""/None falsy — never
bare `bool()`), wired into >BOOL, IF, IF-RUN, WHEN, ANY?, ALL?, and the
Batch 2 predicates. Fix OR/AND to strictly two-operand (array operand
errors toward ANY?/ALL?) and ANY's empty-items2 → false.
TRY / OK? / ERROR? / UNWRAP / UNWRAP-OR belong to the plan's **Phase 2**
(transactional stack, module unwinding, rs try_word_test.rs as the law) —
counted as missing here, implemented there.

**Batch 2 — higher-order & sorting: DONE (feat/word-batch2)**
FILTER (SELECT dropped; record shape + insertion order; with_key), FIND
(short-circuits), COUNT, SORT verified (natural order NULL-last,
comparator = KEY function, non-array passthrough, copy-on-write), SORT-BY
(stable ties), MIN-BY/MAX-BY (null on empty; ties keep earliest),
UNIQUE-BY (keeps first; to_compact_json seen-keys), SORT-U, NUMBERED,
FIRST, TAKE-LAST, MAP-AT (single key or path array, silent misses, empty
path = whole container, numeric-string indexes, copy-on-write), TIMES-RUN
(<REPEAT dropped — no automatic value passing). Grouping fixes:
GROUP-BY / GROUP-BY-FIELD / BY-FIELD group keys coerce like JS object
keys via utils.value_to_key_string (the old str(int()) hack corrupted
float keys); GROUP-BY-FIELD errors properly on NULL records and groups
missing fields under "null"; BY-FIELD skips falsy records via is_truthy;
GROUPS-OF truncates fractional sizes; INDEX passes None through.
Spec: tests/unit/core/test_word_batch2.py; tier2 FIRST/TAKE-LAST
assertions un-deferred. Original spec:
FILTER (rename SELECT; predicate via is_truthy — current code uses raw
Python truthiness at array_module.py:471,482), FIND, COUNT, SORT-BY,
MIN-BY/MAX-BY (null on empty), UNIQUE-BY (keeps first), SORT-U, NUMBERED,
FIRST, TAKE-LAST, MAP-AT (single key or path array, jq `|=`), TIMES-RUN
(( n forthic -- ); drop <REPEAT), GROUP-BY / GROUP-BY-FIELD / BY-FIELD /
GROUPS-OF / KEY-OF / ZIP-WITH content verification after the Batch 0
renames (verify group-key coercion — py does `str(int())` on numeric keys;
match ts), INDEX verify (both lowercase keys — matches), MAP `.outcomes`
(snapshot BEFORE the item push; with Phase 2), FOREACH push_error removal
(composition is `'W' TRY FOREACH`). SORT verify: comparator option is a
KEY FUNCTION (py agrees); py sorts None-last (matches rs's sanctioned
order); check mixed-type ordering.

**Batch 3 — records & JQ paths: DONE (feat/word-batch3)**
JQ@ (null on miss, [] iterates + flattens conditionally, quoted keys,
path arrays, insertion-order record indexing, strict [n] parse), JQ!
(auto-creates by NEXT-segment kind, no [], pads arrays with NULL,
empty path replaces container), JQ-DEL (silent no-ops, no []), MERGE
(shallow, rec2 wins, shared keys keep rec1's position; REC-DEFAULTS
dropped — migration: defaults-first MERGE, noting REC-DEFAULTS also
overrode NULL/""), PICK (keys-list order, missing skipped), OMIT
(stringified drop keys), HAS-KEY? (presence), DELETE (copy-on-write,
integer-only array indexes, negative wraps once; <DEL dropped — it
MUTATED in place), REC>ENTRIES/ENTRIES>REC (insertion-order round-trip
identity; strict pair validation now shared with REC via build_record —
REC no longer accepts malformed pairs). |REC@ was already removed in
Batch 0. py has no prototype-pollution surface, so ts's assert_safe_key
guard has no analog here. Spec: tests/unit/core/test_word_batch3.py;
tier2 DELETE assertion un-deferred. Original spec:
JQ@ (null on miss; `[]` iterates + flattens conditionally), JQ!
(auto-creates by NEXT-segment kind, no `[]`, pads arrays with NULL), JQ-DEL
(silent no-op, no `[]`), MERGE (shallow, rec2 wins; drop REC_DEFAULTS —
migration note: it also overrode None/"" values), PICK (missing keys
skipped), OMIT, HAS-KEY? (key presence, not non-null), DELETE
(copy-on-write; drop <DEL — note py's <DEL MUTATES in place), REC>ENTRIES +
ENTRIES>REC (round-trip identity; INSERTION order per the settled contract
— ts sorts by key as a JS-object-order workaround; the rs divergence is the
sanctioned spec), remove |REC@, RELABEL sorted() removal
(record_module.py:148), strict integer parse for `[n]` path segments (no
leniency). py's REC@ field-array drilling matches ts — keep.

**Batch 4 — strings & interpolation: DONE (feat/word-batch4)**
SUBSTR/SPLICE (JS-slice clamping over code-point indices — host-native
units), STARTS-WITH?/ENDS-WITH?, TRIM-PREFIX/TRIM-SUFFIX (one
occurrence), RE-MATCH? (predicate), RE-REPLACE (JS $n/$&/$$ backrefs
normalized to Python's re.sub template), REPLACE now fully literal
(str.replace — the old re.escape+sub still interpreted backslashes in
the replacement), RE-MATCH verified ([full, g1..], None non-participating,
False no-match — ts parity), RE-MATCH-ALL fixed (group-1-else-full; the
old code errored on group-less patterns), LINES/UNLINES, GREP/GREP-V
(non-string asymmetry), SED, CUT ('' splits into chars), all regex words
compile via a clean "Invalid regex" error.
INTERPOLATE + PRINT REDESIGNED to the settled ${name} contract (ts PR
#41 / rs PR #15): names-only holes (non-name body hard error — templates
can never execute Forthic), ${.name} spelling, \${ escapes, __
reserved, READ-ONLY lookup via new Interpreter.find_variable (miss
renders as null_text default "", creates nothing — the old grammar
MINTED variables on miss), arrays join with separator, records → compact
JSON, [.json TRUE]. The bare-dot grammar is dead. null_text default
changed "null" → "". Spec: tests/unit/core/test_word_batch4.py.
Original spec:
STR-LENGTH (py `len()` = code points — host-native units per contract;
never assert cross-runtime length equality on astral-plane input), SUBSTR
(JS String.slice clamping, negatives from the end), SPLICE,
STARTS-WITH?/ENDS-WITH?, TRIM-PREFIX/TRIM-SUFFIX (one occurrence),
RE-MATCH? (jq `test`, predicate only), RE-REPLACE (regex; REPLACE stays
literal — py's is already literal via re.escape; normalize JS `$n`
backrefs to Python's engine per the rs precedent), RE-MATCH / RE-MATCH-ALL
renames + fixes (py RE-MATCH already returns [full, g1, ...] / False on
no-match like ts — verify non-participating groups render as null;
RE-MATCH-ALL must be group-1-else-full-match — py's `m.group(1)` errors
when the pattern has no groups), LINES/UNLINES, GREP (matching strings
only) / GREP-V (keeps non-strings — deliberate asymmetry), SED
(non-strings pass through), CUT (literal separator; '' splits into chars;
out-of-range field → null). URL-ENCODE/URL-DECODE renames if not done in
Batch 0.
INTERPOLATE + PRINT — the settled `${name}` redesign (port ts PR #41 / rs
PR #15): `${name}` holes (`${.name}` also accepted, body whitespace trims);
holes are variable names ONLY — non-name body is a HARD error (templates
can never execute Forthic); `\${` escapes; `__` names reserved; READ-ONLY
module-stack lookup — a miss renders as null_text (default "") and creates
nothing; arrays join with separator (", ") recursively; records → compact
JSON; `[.json TRUE]` renders anything as compact JSON; PRINT shares
options + rendering, pushes nothing. Deletes py's bare-dot grammar and its
variable-minting lookup (core_module.py:291-342). py has no `{.var}@`
grammar — nothing to remove there.

**Batch 5 — math & datetime round-out: TODO**
RANGE (inclusive; EMPTY if start > end; 10M allocation bound),
FORMAT-FIXED (drop >FIXED; contract is JS toFixed: half-AWAY-from-zero
ties — Python's f-string formatting is half-even, so the naive
`f"{num:.{digits}f}"` py has today is WRONG on ties; digits outside 0..=100
and non-numeric num ERROR), SQRT (negative → NaN — py's math.sqrt RAISES
ValueError today, fix), CLAMP (py's max(min, min(max, value)) matches —
min wins when min > max; verify NaN propagation, Python's max/min are
order-dependent with NaN), ROUND (verify: Python round() is banker's
rounding, JS Math.round is half-up — pin the ts behavior), MOD (verify
Python `%` vs JS `%` on negatives), >INT/>FLOAT fallback behavior vs ts,
DAYS-BETWEEN (pure rename of SUBTRACT-DATES, same date1-date2 sign; drop
the classic — the LAST scheduled classic drop), YEAR, MONTH (1-based),
DAY-OF-WEEK (ISO 1=Mon..7=Sun; strings → null), AM/PM (adjust times;
everything else passes through UNCHANGED, not null — verify py),
USE-MODULES (rename from USE_MODULES + ts options: entries 'name' or
['name' 'prefix']; [.prefixed TRUE] self-prefixes plain names; explicit
pair prefix ALWAYS beats the option; unknown name errors).

## Present-but-verify list: TODO

Words py already registers under the right name whose semantics need
checking (or outright fixing) against the settled contract:

Known-broken, fix required:
- **>BOOL** — FIXED (Phase 1): `is_truthy` in forthic/utils.py.
- **@** core_module.py:146 — must be READ-ONLY; undeclared string name →
  UnknownVariableError; miss creates NOTHING. `!`/`!@` keep get-or-create
  (core_module.py:138,155 are correct). Still open (Batch/verify).
- **Key-sorting sites** — FIXED (Phase 1): the six array_module sites
  (NTH, LAST, SLICE, TAKE, DROP→SKIP, UNPACK) use insertion order;
  TAKE/DROP return records for records. RELABEL's sorted() stays (array
  arm, matches ts classic — inventory correction).
- **SLICE** — FIXED (Phase 1): 10M span guard added (ts message shape).
- **TAKE** — FIXED (Phase 1): record in → record out, insertion order,
  push_rest intact. ts's with_key remains declared-but-dead — not ported.
- **OR/AND** — element tests + two-value selection now use is_truthy
  (Phase 1); the ARITY change (array operand errors toward ANY?/ALL?)
  is still Batch 1. **ANY** empty-items2 → false — FIXED (Phase 1).

Verify against ts, expected mostly fine:
- **MEAN** math_module.py:150 — full polymorphic dispatch is present
  (falsy → 0, non-array as-is, single element before null filtering, null
  skip, strings → frequency record, records → field-wise mean). Verify
  corner order and fix the `set()` used for record keys (order).
- **SUM** — matches (non-numeric/None skip semantics vs ts to confirm).
- **UNIQUE** array_module.py:487 — dict.fromkeys raises on unhashables;
  decide structural-equality policy (rs sanctioned values_equal).
- **KEY-OF / GROUP-BY key coercion** — py `==` and `str(int())`; align
  with ts / rs value_to_key_string precedent.
- **FLATTEN** array_module.py:912 — already ts-shaped; verify depth-0,
  and the `{}`-as-leaf edge (py's is_record treats empty dict as scalar).
- **ZIP / ZIP-WITH** record arms vs ts.
- **REC@** drilling (field or field-array) — matches ts, keep.
- **DEFAULT** — None/"" → default; matches ts (null/undefined/"").
- **RE-MATCH** — [full, groups...] / False-on-no-match matches ts; verify
  null for non-participating groups.
- **REPLACE** — literal via re.escape; matches post-scrub ts (regex moved
  to RE-REPLACE). Keep.
- **NOW / TODAY / >DATE / >DATETIME / AT / >TIMESTAMP /
  TIMESTAMP>DATETIME** — tz plumbing uses interp.get_timezone() + ZoneInfo
  (audit says looks right). Verify the #35 specifics: input trim; ISO
  datetimes with explicit offset take the date AS WRITTEN; trailing-Z
  instants resolve in the INTERPRETER timezone; month-name forms parse;
  `0 >DATE` stays NULL (deliberate falsy asymmetry with `0 >DATETIME` =
  epoch); strict parsing otherwise (no new-Date() leniency).
- **AM/PM** datetime_module.py:77,93 — verify non-time inputs pass through
  UNCHANGED (not null).
- **PEEK! / STACK!** — verify stop-execution semantics match ts.
- **NTH / FIRST-adjacent corners** — n=None/container=None → null matches;
  record arm after de-sorting must use insertion order.
- **MAP** — with_key/depth match ts; remove push_error + dead push_rest;
  add `.outcomes` (Phase 2); `interps` optional (see Never port).
- **EXPORT / PROFILE-* / SHUFFLE / ROTATE / INFINITY / UNIFORM-RANDOM /
  RE-MATCH-GROUP / E / PI** — dispositions per the classic section above.
