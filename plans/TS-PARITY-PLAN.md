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
9. **Transports exist** (jsonrpc + grpc dirs) — verify the ErrorInfo wire
   shape {message, error_type, context, word_location} and serializer
   type tags against the ts/rs golden fixtures.
10. **819 test functions** across 42 files — real coverage to build on.
11. **No CI** (no .github/workflows) — same gap rs had.

## Phases

Rhythm per phase (the rs cadence): implement → gates → update plans docs →
commit → annotate diff (hunk) → review → PR → merge → next.
**Gates**: `pytest`, `ruff check`, `mypy` (pyproject already configures
ruff + mypy for py310), plus cross-runtime smoke once wired.

- **Phase 0 — CI + inventory.** Add GitHub Actions (pytest/ruff/mypy).
  Run the word-inventory agent against post-scrub ts to produce
  `plans/WORD-INVENTORY.md` (py edition): word-by-word delta, collision
  table (DROP/SKIP, CONCAT, RANGE, FLATTEN), classic-word list, batch
  assignments. The rs inventory is the template; expect the same shape.
- **Phase 1 — Correctness tier.** is_truthy sweep (audit item 1); remove
  key-sorting (item 2); >STR/stringification contract (records → compact
  JSON, None → ""); values-equal semantics for temporal/record types;
  error-formatter crash-proofing; reset() completeness. Port the rs
  tier1/tier2 test files as the spec.
- **Phase 2 — Error handling.** TRY family (TRY, OK?, ERROR?, UNWRAP,
  UNWRAP-OR) with transactional stack + module unwinding; remove
  push_error; MAP `.outcomes`. The rs try_word_test.rs pins the laws.
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
