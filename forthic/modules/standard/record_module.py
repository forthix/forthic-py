"""Record module - Record (object/dictionary) manipulation operations.

Provides operations for working with key-value data structures.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

from ...decorators import DecoratedModule, register_module_doc
from ...decorators import ForthicWord as WordDecorator


class RecordModule(DecoratedModule):
    """Record (object/dictionary) manipulation operations for working with key-value data structures."""

    def __init__(self) -> None:
        super().__init__("record")
        register_module_doc(
            RecordModule,
            """
Record (object/dictionary) manipulation operations for working with key-value data structures.

## Categories
- Core: REC, REC@, <REC!, ENTRIES>REC, REC>ENTRIES
- Transform: RELABEL, INVERT-KEYS, MERGE, PICK, OMIT, DELETE
- JQ paths: JQ@, JQ!, JQ-DEL (use "[].field" JQ@ to map a field over an array of records)
- Query: HAS-KEY?
- Access: KEYS, VALUES
            """,
        )

    @staticmethod
    def build_record(key_vals: Any, word_name: str) -> dict:
        """Build a record from [key, value] pairs, validating pair shape.
        Duplicate keys: later wins, first position kept (dict semantics)."""
        _key_vals = key_vals if key_vals else []
        result: dict = {}
        for index, pair in enumerate(_key_vals):
            if not isinstance(pair, list):
                raise ValueError(
                    f"{word_name} requires each pair to be a [key, value] array with exactly 2 "
                    f"elements; pair at index {index} is not an array (got {type(pair).__name__})."
                )
            if len(pair) != 2:
                key = repr(pair[0]) if len(pair) >= 1 else "(none)"
                raise ValueError(
                    f"{word_name} requires each pair to be a [key, value] array with exactly 2 "
                    f"elements; pair at index {index} has {len(pair)} element(s) (key: {key})."
                )
            result[pair[0]] = pair[1]
        return result

    @staticmethod
    def drill_for_value(record: Any, fields: list[str]) -> Any:
        """Helper function to drill down into nested record structure.

        Args:
            record: The record to drill into
            fields: Array of field names to traverse

        Returns:
            The value at the end of the field path, or None if not found
        """
        result = record
        for field in fields:
            if result is None:
                return None
            if isinstance(result, dict):
                result = result.get(field)
            elif isinstance(result, list):
                try:
                    result = result[int(field)]
                except (ValueError, IndexError, TypeError):
                    return None
            else:
                return None
        return result

    # ==================
    # Core Operations
    # ==================

    @WordDecorator("( key_vals:any[] -- rec:any )", "Create record from [[key, val], ...] pairs")
    async def REC(self, key_vals: list) -> dict:
        return RecordModule.build_record(key_vals, "REC")

    @WordDecorator("( rec:any field:any -- value:any )", "Get value from record by field or array of fields", "REC@")
    async def REC_at(self, rec: Any, field: Any) -> Any:
        if not rec:
            return None

        fields = [field]
        if isinstance(field, list):
            fields = field

        result = RecordModule.drill_for_value(rec, fields)
        return result

    @WordDecorator("( rec:any value:any field:any -- rec:any )", "Set value in record at field path", "<REC!")
    async def l_REC_bang(self, rec: Any, value: Any, field: Any) -> dict:
        _rec = rec if rec else {}

        fields: list[str] = []
        if isinstance(field, list):
            fields = field
        else:
            fields = [field]

        def ensure_field(record: dict, field_name: str) -> dict:
            res = record.get(field_name)
            if res is None:
                res = {}
                record[field_name] = res
            return res

        cur_rec = _rec
        # Drill down up until the last value
        for i in range(len(fields) - 1):
            cur_rec = ensure_field(cur_rec, fields[i])

        # Set the value at the right depth within rec
        cur_rec[fields[-1]] = value

        return _rec

    # ==================
    # Transform Operations
    # ==================

    @WordDecorator("( container:any old_keys:any[] new_keys:any[] -- container:any )", "Rename record keys")
    async def RELABEL(self, container: Any, old_keys: list, new_keys: list) -> Any:
        if not container:
            return container

        if len(old_keys) != len(new_keys):
            raise ValueError("RELABEL: old_keys and new_keys must be same length")

        new_to_old: dict = {}
        for i in range(len(old_keys)):
            new_to_old[new_keys[i]] = old_keys[i]

        result: Any
        if isinstance(container, list):
            result = []
            for k in sorted(new_to_old.keys()):
                result.append(container[new_to_old[k]])
        else:
            result = {}
            for k in new_to_old.keys():
                result[k] = container[new_to_old[k]]

        return result

    @WordDecorator("( record:any -- inverted:any )", "Invert two-level nested record structure", "INVERT-KEYS")
    async def INVERT_KEYS(self, record: dict) -> dict:
        result: dict = {}
        for first_key in record.keys():
            sub_record = record[first_key]
            for second_key in sub_record.keys():
                value = sub_record[second_key]
                if second_key not in result:
                    result[second_key] = {}
                result[second_key][first_key] = value

        return result

    # ==================
    # JQ-style path access
    # ==================

    @staticmethod
    def _parse_jq_path(path: Any) -> list[tuple]:
        """Parse a jq-style path into segments: ("field", name),
        ("index", n), or ("iterate",). Path arrays are dynamic keys.
        Strict integer parse in [n] — ts's parseInt('1x') leniency is
        rejected by design (cross-runtime contract)."""
        if isinstance(path, list):
            segments: list[tuple] = []
            for part in path:
                if isinstance(part, int) and not isinstance(part, bool):
                    segments.append(("index", part))
                else:
                    segments.append(("field", str(part)))
            return segments

        text = "" if path is None else str(path)
        if text in ("", "."):
            return []
        if text.startswith("."):
            text = text[1:]

        segments = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == ".":
                i += 1
                continue
            if ch == "[":
                i += 1
                if i >= len(text):
                    raise ValueError(f"JQ path: unclosed '[' in \"{path}\"")
                if text[i] == "]":
                    segments.append(("iterate",))
                    i += 1
                elif text[i] in ("'", '"'):
                    quote = text[i]
                    i += 1
                    name = ""
                    while i < len(text) and text[i] != quote:
                        name += text[i]
                        i += 1
                    if i >= len(text):
                        raise ValueError(f"JQ path: unclosed quote in \"{path}\"")
                    i += 1
                    if i >= len(text) or text[i] != "]":
                        raise ValueError(f"JQ path: expected ']' after quoted key in \"{path}\"")
                    i += 1
                    segments.append(("field", name))
                else:
                    num = ""
                    while i < len(text) and text[i] != "]":
                        num += text[i]
                        i += 1
                    if i >= len(text):
                        raise ValueError(f"JQ path: unclosed '[' in \"{path}\"")
                    i += 1
                    if not re.fullmatch(r"-?\d+", num):
                        raise ValueError(f"JQ path: invalid index \"{num}\" in \"{path}\"")
                    segments.append(("index", int(num)))
            else:
                name = ""
                while i < len(text) and text[i] not in (".", "["):
                    name += text[i]
                    i += 1
                if name:
                    segments.append(("field", name))
        return segments

    @staticmethod
    def _jq_get(container: Any, segments: list[tuple]) -> Any:
        if not segments:
            return container
        if container is None:
            return None

        first, rest = segments[0], segments[1:]

        if first[0] == "iterate":
            if isinstance(container, list):
                items = container
            elif isinstance(container, dict):
                # Insertion order, consistent with KEYS/NTH/FIRST
                items = list(container.values())
            else:
                return []

            rest_iterates = any(seg[0] == "iterate" for seg in rest)
            result = []
            for item in items:
                if not rest:
                    result.append(item)
                else:
                    r = RecordModule._jq_get(item, rest)
                    if rest_iterates and isinstance(r, list):
                        result.extend(r)
                    else:
                        result.append(r)
            return result

        if first[0] == "field":
            if isinstance(container, dict):
                return RecordModule._jq_get(container.get(first[1]), rest)
            return None

        # index
        n = first[1]
        if isinstance(container, list):
            idx = n + len(container) if n < 0 else n
            if idx < 0 or idx >= len(container):
                return None
            return RecordModule._jq_get(container[idx], rest)
        if isinstance(container, dict):
            keys = list(container.keys())
            idx = n + len(keys) if n < 0 else n
            if idx < 0 or idx >= len(keys):
                return None
            return RecordModule._jq_get(container[keys[idx]], rest)
        return None

    @staticmethod
    def _seg_key(seg: tuple) -> Any:
        if seg[0] in ("field", "index"):
            return seg[1]
        raise ValueError("JQ: [] iteration not supported here")

    @staticmethod
    def _checked_set_key(cur: Any, seg: tuple, key: Any) -> None:
        """Guard a single set step: arrays take non-negative integer indexes
        only, and out-of-range indexes pad with null (no JS holes —
        cross-runtime contract)."""
        if isinstance(cur, list):
            if seg[0] != "index":
                raise ValueError(f"JQ!: cannot set field '{key}' on an array")
            if key < 0:
                raise ValueError(f"JQ!: negative set index {key}")
            while len(cur) < key:
                cur.append(None)

    @staticmethod
    def _jq_set(container: Any, segments: list[tuple], value: Any) -> Any:
        cur = container
        for i in range(len(segments) - 1):
            seg = segments[i]
            nxt = segments[i + 1]
            key = RecordModule._seg_key(seg)
            RecordModule._checked_set_key(cur, seg, key)

            if isinstance(cur, list) and key == len(cur):
                cur.append(None)
            child = cur[key] if (isinstance(cur, dict) and key in cur) or (
                isinstance(cur, list) and 0 <= key < len(cur)
            ) else None
            if not isinstance(child, (list, dict)):
                child = [] if nxt[0] == "index" else {}
                cur[key] = child
            cur = child

        last_seg = segments[-1]
        last_key = RecordModule._seg_key(last_seg)
        RecordModule._checked_set_key(cur, last_seg, last_key)
        if isinstance(cur, list) and last_key == len(cur):
            cur.append(value)
        else:
            cur[last_key] = value
        return container

    @staticmethod
    def _jq_del(container: Any, segments: list[tuple]) -> Any:
        cur = container
        for seg in segments[:-1]:
            key = RecordModule._seg_key(seg)
            if isinstance(cur, dict):
                cur = cur.get(key)
            elif isinstance(cur, list) and isinstance(key, int) and 0 <= key < len(cur):
                cur = cur[key]
            else:
                return container
        if not isinstance(cur, (list, dict)):
            return container

        last = segments[-1]
        if last[0] == "field":
            if isinstance(cur, dict):
                cur.pop(last[1], None)
        else:
            n = last[1]
            if isinstance(cur, list):
                idx = n + len(cur) if n < 0 else n
                if 0 <= idx < len(cur):
                    del cur[idx]
            elif isinstance(cur, dict):
                cur.pop(n, None)
        return container

    @WordDecorator(
        "( container:any path:any -- value:any )",
        "Get value at jq-style path (e.g., .users[].name). Returns null on miss; [] iterates and flattens. Path arrays accepted for dynamic keys.",
        "JQ@",
    )
    async def JQ_at(self, container: Any, path: Any) -> Any:
        segments = RecordModule._parse_jq_path(path)
        return RecordModule._jq_get(container, segments)

    @WordDecorator(
        "( container:any value:any path:any -- container:any )",
        "Set value at jq-style path. Auto-creates missing intermediates (record for field, array for index). [] iteration not supported.",
        "JQ!",
    )
    async def JQ_bang(self, container: Any, value: Any, path: Any) -> Any:
        segments = RecordModule._parse_jq_path(path)
        if any(seg[0] == "iterate" for seg in segments):
            raise ValueError("JQ!: [] iteration not supported in set paths")
        if not segments:
            return value

        _container = container
        if not isinstance(_container, (list, dict)):
            _container = [] if segments[0][0] == "index" else {}
        return RecordModule._jq_set(_container, segments, value)

    @WordDecorator(
        "( container:any path:any -- container:any )",
        "Delete value at jq-style path. No-op if path doesn't exist. [] iteration not supported.",
        "JQ-DEL",
    )
    async def JQ_DEL(self, container: Any, path: Any) -> Any:
        segments = RecordModule._parse_jq_path(path)
        if any(seg[0] == "iterate" for seg in segments):
            raise ValueError("JQ-DEL: [] iteration not supported in delete paths")
        if not segments or container is None:
            return container
        return RecordModule._jq_del(container, segments)

    # ==================
    # Merge / Pick / Omit / Delete
    # ==================

    @WordDecorator(
        "( rec1:any rec2:any -- merged:any )",
        "Shallow merge two records. Keys present in rec2 override rec1 (shared keys keep rec1's position).",
        "MERGE",
    )
    async def MERGE(self, rec1: Any, rec2: Any) -> dict:
        a = rec1 if isinstance(rec1, dict) else {}
        b = rec2 if isinstance(rec2, dict) else {}
        return {**a, **b}

    @WordDecorator(
        "( rec:any keys:any[] -- rec:any )",
        "Return a new record containing only the listed keys (missing keys are skipped).",
        "PICK",
    )
    async def PICK(self, rec: Any, keys: Any) -> dict:
        if not isinstance(rec, dict):
            return {}
        ks = keys if isinstance(keys, list) else []
        return {k: rec[k] for k in ks if k in rec}

    @WordDecorator(
        "( rec:any keys:any[] -- rec:any )",
        "Return a new record without the listed keys.",
        "OMIT",
    )
    async def OMIT(self, rec: Any, keys: Any) -> dict:
        if not isinstance(rec, dict):
            return {}
        # Stringify drop keys: record keys are strings, so a numeric key in
        # the drop list (e.g. [ 1 ] OMIT) must match key "1" — an identity
        # set would silently miss it (cross-runtime contract)
        drop = {str(k) for k in (keys if isinstance(keys, list) else [])}
        return {k: v for k, v in rec.items() if str(k) not in drop}

    @WordDecorator(
        "( rec:any key:any -- bool:boolean )",
        "Returns true if rec has the given key. Distinct from REC@ NULL == — handles intentional null values correctly.",
        "HAS-KEY?",
    )
    async def HAS_KEY_q(self, rec: Any, key: Any) -> bool:
        if not isinstance(rec, dict):
            return False
        return key in rec

    @WordDecorator(
        "( container:any key:any -- container:any )",
        "Delete key from record or index from array (copy-on-write; classic <DEL mutated in place)",
        "DELETE",
    )
    async def DELETE(self, container: Any, key: Any) -> Any:
        if not container:
            return container

        if isinstance(container, list):
            # Integer keys only (no NaN->0 splice surprise). Negative wraps
            # once; out-of-range is a no-op. Copy first: mutation would
            # alias the input.
            if isinstance(key, bool) or not isinstance(key, int):
                raise ValueError(f"DELETE on an array requires an integer index, got {key!r}")
            copy = list(container)
            idx = key + len(copy) if key < 0 else key
            if 0 <= idx < len(copy):
                del copy[idx]
            return copy
        rec_copy = dict(container)
        rec_copy.pop(key, None)
        return rec_copy

    # ==================
    # Entries
    # ==================

    @WordDecorator(
        "( pairs:any[] -- rec:any )",
        "Build a record from an array of [key, value] pairs. Alias of REC, surfaced for symmetry with REC>ENTRIES.",
        "ENTRIES>REC",
    )
    async def ENTRIES_to_REC(self, pairs: Any) -> dict:
        return RecordModule.build_record(pairs, "ENTRIES>REC")

    @WordDecorator(
        "( rec:any -- pairs:any[] )",
        "Convert a record to an array of [key, value] pairs in insertion order. Inverse of ENTRIES>REC / REC.",
        "REC>ENTRIES",
    )
    async def REC_to_ENTRIES(self, rec: Any) -> list:
        if not isinstance(rec, dict):
            return []
        return [[k, v] for k, v in rec.items()]

    # ==================
    # Access Operations
    # ==================

    @WordDecorator("( container:any -- keys:any[] )", "Get keys from record or indices from array")
    async def KEYS(self, container: Any) -> list:
        _container = container if container else []

        result: list
        if isinstance(_container, list):
            result = list(range(len(_container)))
        else:
            result = list(_container.keys())

        return result

    @WordDecorator("( container:any -- values:any[] )", "Get values from record or elements from array")
    async def VALUES(self, container: Any) -> list:
        _container = container if container else []

        result: list
        if isinstance(_container, list):
            result = _container
        else:
            result = list(_container.values())

        return result
