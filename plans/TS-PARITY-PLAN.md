# forthic-py Parity Scrub Plan (2026-07-12)

Bring forthic-py from its v0.5.0 parity milestone (December 2025) up to the
settled cross-runtime contract. This mirrors the forthic-rs scrub
(December 2025 → July 2026, PRs #2–#19), which is the playbook — but the
second pass is much cheaper because every contract decision has already
been made and documented. **Post-scrub forthic-ts is the spec**; the
contract decisions live in `forthic-rs/plans/WORD-INVENTORY.md` and
`forthic-rs/plans/TS-PARITY-BACKLOG.md`, and the rs divergence tests are
executable contract specs.

## Settled decisions to inherit (do not re-litigate)

- **JS truthiness everywhere** (`>BOOL`, IF, ANY?, ALL?, WHEN): empty
  containers are TRUTHY, NaN is falsy, 0/""/None falsy. Python's native
  `bool()` disagrees on empty containers — never use it directly.
- **Host-native string units**: py measures in code points (`len(str)`),
  same as rs; ts uses UTF-16 units. Never assert cross-runtime
  position/length equality on astral-plane inputs.
- **Records are insertion-ordered** in every word (iteration, indexing,
  KEYS, REC>ENTRIES, JQ@). Python dicts already are — the work is
  *removing* key-sorting, not adding order.
- **Strict parsing**: no parseInt/new Date() leniency. Malformed ints in
  JQ paths error; >DATE takes a fixed format list.
- **None/null only** — "null" never "undefined"; ts's UNDEFINED word is
  ts-only host interop and is never ported.
- **TRY error handling** (Rust Result semantics): `'CODE' TRY` →
  `{"ok": v}` / `{"error": {message, error_type}}`; transactional stack;
  `'CODE' TRY UNWRAP ≡ CODE`; module-stack unwinding. `push_error` is
  REMOVED from the contract. MAP gets an `.outcomes` option (snapshot
  BEFORE the item push). No MAP-OK/MAP-ERR.
- **Interpolation**: `${name}` holes only (dot optional: `${.name}`),
  names-only — a non-name body (`${1 + 2}`) is a HARD error so templates
  can never execute Forthic; READ-ONLY lookup (a miss renders as
  null_text, default "", and creates nothing); `\${` escapes; `__` names
  reserved. One INTERPOLATE in core; PRINT shares it. Both the bare-dot
  and `{.var}@` grammars are dead.
- **Classic words with canonical replacements are dropped** (no aliases,
  pre-1.0): POP→DROP, IDENTITY→NOP, IN→CONTAINS?, <DEL→DELETE,
  REC-DEFAULTS→MERGE, SUBTRACT-DATES→DAYS-BETWEEN. The 9 no-replacement
  classics stay (XOR, NAND, RELABEL, INVERT-KEYS, DATE>INT,
  JSON-PRETTIFY, /R, URL-ENCODE, URL-DECODE). Tombstone-test each drop.
- **`@` is read-only** (unknown variable errors, never creates); only `!`
  and `!@` get-or-create. OR/AND are strictly two-operand (arrays error
  toward ANY?/ALL?). MEAN is polymorphic (numbers/strings/records).
  Datetime words resolve in the INTERPRETER timezone; >DATE's #35 rule:
  trailing-Z instants resolve in the interpreter tz.
- **Word docs are data**: stack effect + description carried per word,
  compile/registration-enforced where possible, served by docs generation
  and jsonrpc getModuleInfo. py's @ForthicWord decorators already do this
  — keep them; the sweep is about coverage, not mechanism.

## Audit snapshot (2026-07-12, verified against py code)

Confirmed problems:
1. **Truthiness bug (the rs bug, present here)**: `boolean_module.py:173`
   `return bool(a)` — empty list/dict falsy under Python, truthy under
   the contract. Sweep every truthiness site into one `is_truthy` helper.
2. **Key-sorting violates insertion order**: `array_module.py:85,102,150`
   and `record_module.py:148` call `sorted(container.keys())`. Remove;
   add regression tests (rs tier2 tests are the spec).
3. **TRY family MISSING**; `push_error` still present
   (`word_options.py`, `array_module.py`) — must be removed with TRY's
   arrival, plus MAP `.outcomes`.
4. **Old interpolation grammar**: `core_module.py:40-55` documents
   bare-dot `"Hello .name" INTERPOLATE`. Needs the `${name}` redesign
   (port from ts core_module.ts / rs core.rs — both shipped it).
5. **JQ path words MISSING** (no JQ@/JQ!/JQ-DEL). Port from rs
   jq_path.rs / ts record_module.ts.
6. **Classic words still registered**: SUBTRACT-DATES at
   `datetime_module.py:361`; audit for the full classic list (POP, IN,
   <DEL, REC-DEFAULTS...) and the DROP/SKIP + CONCAT + RANGE + FLATTEN
   collision fixes from rs Batch 0.

Confirmed good (verify, don't rebuild):
7. **Timezone handling looks right**: datetime_module.py uses
   `interp.get_timezone()` + ZoneInfo throughout — check >DATE #35
   (Z-instants) and AT/>DATETIME specifics rather than assuming.
8. **Word metadata mechanism exists**: @ForthicWord/@ForthicDirectWord
   decorators with stack effects + descriptions (ts-style). ~50 decorated
   words counted in standard modules vs 177 in ts/rs — the gap is
   inventory, not infrastructure. record_module.py shows 0 decorators —
   check how it registers.
9. **Transport exists** (jsonrpc; gRPC support was removed in Phase 0 —
   JSON-RPC is the transport) — verify the ErrorInfo wire shape
   {message, error_type, context, word_location} and serializer type
   tags against the ts/rs golden fixtures.
10. **819 test functions** across 42 files — real coverage to build on.
    (Phase 0: 749 remain after the gRPC removal — the deleted grpc/
    multi-runtime tests accounted for the rest.)
11. **No CI** (no .github/workflows) — same gap rs had. (Closed in
    Phase 0.)

## Phases

Rhythm per phase (the rs cadence): implement → gates → update plans docs →
commit → annotate diff (hunk) → review → PR → merge → next.
**Gates**: `pytest`, `ruff check`, `mypy` (pyproject already configures
ruff + mypy for py310), plus cross-runtime smoke once wired.

- **Phase 0 — CI + inventory. DONE (2026-07-12).** GitHub Actions added
  (pytest on py 3.10–3.12 + JSON-RPC smoke; ruff; mypy — all green, via
  uv). `plans/WORD-INVENTORY.md` (py edition) produced and spot-verified:
  73 canonical words missing, MORE collisions than rs (variable-arity
  +/*/MAX/MIN/OR/AND survive in py), a py-specific underscore-name bug
  (14 words registered as GROUP_BY etc.), all 34 ts classics present,
  |REC@ still live. Scope change made in this phase: **gRPC support
  removed entirely** (owner call — JSON-RPC is the transport);
  module_loader + Remote*Error moved into forthic.jsonrpc, servicer made
  public (JsonRpcServicer), grpc extra/script/Makefile targets deleted.
  Dev env moved to uv (uv venv/.venv; uv.lock not committed).
- **Phase 1 — Correctness tier. DONE (2026-07-12).** is_truthy +
  values_equal + to_forthic_string/to_compact_json live in
  forthic/utils.py. Swept >BOOL, OR/AND (element tests + JS ||/&&
  selection), NOT/XOR/NAND, SELECT predicate; ==/!=/IN/ANY/ALL use
  values_equal (bools ≠ numbers, int/float unify, datetimes tz-sensitive
  like ts ISO comparison, structural records); ANY empty-items2 → false.
  Removed the six array_module key-sorting sites (RELABEL's sorted()
  turned out to MATCH ts classic — kept); TAKE/DROP return records for
  records; SLICE gained the 10M span guard; UNPACK insertion order;
  DIFFERENCE/INTERSECTION rebuilt on ts's set_op contract (record left =
  PICK/OMIT, array-left-record-right tests against values). >STR does JS
  semantics (None → "", records → compact JSON); >JSON compact like
  JSON.stringify. Error formatter crash-proofed (caret math clamped);
  IntentionalStopError passes through definitions unwrapped; reset()
  clears tokenizer stack + previous token. Specs ported to
  tests/unit/core/test_tier1_correctness.py + test_tier2_record_semantics.py
  (TAKE-LAST/DELETE/FIRST assertions deferred to their batches).
  RELABEL/<DEL's `if not container` guards left for their batch work.
- **Phase 2 — Error handling. DONE (2026-07-12).** TRY, OK?, ERROR?,
  UNWRAP, UNWRAP-OR in core (transactional stack via raw-items snapshot,
  module-stack unwinding, ts payload rule: top-of-stack if the run
  changed the stack, ok:null for no-net-effect). Shared
  `run_to_outcome` in forthic/utils.py powers both TRY and MAP's
  `.outcomes` option (snapshot BEFORE the item push). push_error removed
  from MAP and FOREACH (composition is `'W' TRY FOREACH`); MAP's dead
  push_rest deleted; MAP's depth descent fixed to map scalar leaves like
  ts (it used to crash descending them as records). rs try_word_test.rs
  ported to tests/unit/core/test_try_word.py (19 tests).
  **Two py findings for later phases:** (1) the @ForthicWord decorator
  never pushes None returns, so any decorated word whose result is
  legitimately NULL strands the stack (`NULL REVERSE`, `[] LAST`, ...) —
  UNWRAP/UNWRAP-OR sidestep it as direct words; needs an infrastructure
  decision (inventory flagged). (2) a stray `}` at app-module level does
  NOT error (rs errors there) — Phase 5 verify item.
- **Phase 3 — Word batches.** Batch 0 collisions first, then the gap
  groups per the Phase 0 inventory (JQ paths, records round-out,
  higher-order/sorting deltas, strings/regex/shell words, math/datetime
  round-out incl. DAYS-BETWEEN + classic drops, USE-MODULES options).
  Reuse the rs batch specs; spec-extraction agents per batch only where
  the rs plans are thin.
- **Phase 4 — Interpolation redesign.** `${name}` contract into core;
  delete the bare-dot grammar (and `{.var}@` if present); PRINT shares.
  Port ts PR #41 / rs PR #15 directly.
- **Phase 5 — Verify pass.** The py edition of present-but-verify: @
  read-only, OR/AND arity, MEAN dispatch, datetime specifics (#35 rule),
  TAKE/SLICE bounds — plus anything Phase 0 flags as
  present-but-unverified.
- **Phase 6 — Wire + capstone.** Cross-runtime smoke (py server driven by
  the ts client, like rs's `make smoke-ts`; ideally also py↔rs);
  docstring coverage sweep to match the 177-word documented surface
  (mechanism exists — decorate everything, wire getModuleInfo if it
  serves placeholders); README rewrite + version bump (v0.5.0 → v0.6.0,
  matching the rs convention of versioning by parity milestone).

## Known py-specific watchpoints

- `bool()`/`len()`-based conditionals hiding anywhere a truthiness or
  emptiness check happens — grep broadly, not just boolean_module.
- Integer vs float: `/` is float division in py3 (matches JS); `//` and
  `%` semantics differ from JS for negatives — check MOD against the ts
  contract.
- `sorted()` on dict keys was the JS-object-order workaround ts needed;
  py never needed it — treat every instance as a bug.
- pandas_module is py-only host interop (like ts's fs module): document
  as non-portable, exclude from the portable-core inventory.
- Async: py interpreter may be async (ts is); the sync-interpreter
  decision was rs-specific. Don't "fix" py's async — the contract is
  behavior, not architecture.

## Effort estimate

Roughly half the rs scrub: the decisions, specs, tests-as-contracts, and
batch structure all transfer; py starts with working timezone handling,
insertion-ordered dicts, a metadata mechanism, two transports, and 819
tests. The big-ticket items are TRY, JQ paths, the interpolation
redesign, and the truthiness/ordering correctness pass.
