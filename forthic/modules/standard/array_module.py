"""Array module - Array and collection operations.

Provides array manipulation including mapping, filtering, and grouping.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...interpreter import Interpreter

from ...decorators import DecoratedModule, ForthicDirectWord, register_module_doc
from ...decorators import ForthicWord as WordDecorator
from ...utils import (
    is_truthy,
    run_to_outcome,
    to_compact_json,
    value_to_key_string,
    values_equal,
)


def _as_index(value: Any) -> int | None:
    """ts Number(head) coercion for MAP-AT array indexes: numeric strings
    work as indexes; anything non-integral is a miss."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return int(f) if f.is_integer() else None


# Generous ceiling on how many elements a single word may materialize from
# caller-supplied sizes (SLICE, RANGE). Fails fast instead of OOMing the host.
MAX_MATERIALIZED_ELEMENTS = 10_000_000


class ArrayModule(DecoratedModule):
    """Array and collection operations for manipulating arrays and records."""

    def __init__(self) -> None:
        super().__init__("array")
        register_module_doc(
            ArrayModule,
            """
Array and collection operations for manipulating arrays and records.

## Categories
- Access: NTH, FIRST, LAST, SLICE, TAKE, TAKE-LAST, SKIP, LENGTH, INDEX, KEY-OF
- Transform: MAP, MAP-AT, REVERSE
- Combine: APPEND, ZIP, ZIP-WITH
- Filter: FILTER, UNIQUE, UNIQUE-BY, DIFFERENCE, INTERSECTION, UNION
- Sort: SORT, SORT-BY, SORT-U
- Search: FIND, COUNT
- Extrema: MIN-BY, MAX-BY
- Indexing: NUMBERED
- Group: BY-FIELD, GROUP-BY, GROUP-BY-FIELD, GROUPS-OF
- Iteration: FOREACH, REDUCE, UNPACK, FLATTEN, TIMES-RUN

## Options
Several words support options via the ~> operator using syntax: [.option_name value ...] ~> WORD
- with_key: Push index/key before value (MAP, FOREACH, GROUP-BY, FILTER)
- depth: Recursion depth for nested operations (MAP, FLATTEN)
- outcomes: Map each element to {ok: value} / {error: info} (MAP)
- push_rest: Push remaining items after operation (TAKE)
- comparator: Custom comparison function as Forthic string (SORT)

## Examples
[10 20 30] '2 *' MAP
[10 20 30] '+ 2 *' [.with_key TRUE] ~> MAP
[[[1 2]] [[3 4]]] [.depth 1] ~> FLATTEN
[3 1 4 1 5] [.comparator "-1 *"] ~> SORT
[1 2 3] '2 *' [.outcomes TRUE] ~> MAP
            """,
        )

    # ==================
    # Access
    # ==================

    @WordDecorator("( container:any -- length:number )", "Length of an array or record. For strings, use STR-LENGTH.")
    async def LENGTH(self, container: Any) -> int:
        if container is None:
            return 0
        if isinstance(container, list):
            return len(container)
        if isinstance(container, str):
            raise ValueError("LENGTH operates on arrays and records. For strings, use STR-LENGTH.")
        if isinstance(container, dict):
            return len(container.keys())
        raise ValueError("LENGTH operates on arrays and records.")

    @ForthicDirectWord("( container:any n:number -- item:any )", "Get nth element from array or record")
    async def NTH(self, interp: Interpreter) -> None:
        n = interp.stack_pop()
        container = interp.stack_pop()

        if n is None or container is None:
            interp.stack_push(None)
            return

        if isinstance(container, list):
            if n < 0 or n >= len(container):
                interp.stack_push(None)
            else:
                interp.stack_push(container[n])
        else:
            keys = list(container.keys())
            if n < 0 or n >= len(keys):
                interp.stack_push(None)
            else:
                key = keys[n]
                interp.stack_push(container[key])

    @WordDecorator("( container:any -- item:any )", "Get first element from array or record (insertion order for records)")
    async def FIRST(self, container: Any) -> Any:
        if container is None:
            return None
        if isinstance(container, list):
            return container[0] if container else None
        keys = list(container.keys())
        return container[keys[0]] if keys else None

    @WordDecorator("( container:any -- item:any )", "Get last element from array or record")
    async def LAST(self, container: Any) -> Any:
        if container is None:
            return None

        if isinstance(container, list):
            if len(container) == 0:
                return None
            return container[-1]
        else:
            keys = list(container.keys())
            if len(keys) == 0:
                return None
            return container[keys[-1]]

    @WordDecorator("( container:any start:number end:number -- result:any )", "Extract slice from array or record")
    async def SLICE(self, container: Any, start: int, end: int) -> Any:
        _container = container if container is not None else []

        start = int(start)
        end = int(end)

        if isinstance(_container, list):
            length = len(_container)
        else:
            length = len(_container.keys())

        def normalize_index(index: int) -> int:
            if index < 0:
                return index + length
            return index

        start = normalize_index(start)
        end = normalize_index(end)

        # SLICE pads out-of-range indexes with nulls, so a huge end index
        # would materialize a huge array. Guard the span before building it.
        span = abs(end - start) + 1
        if span > MAX_MATERIALIZED_ELEMENTS:
            raise ValueError(
                f"SLICE span {span} is too large (limit {MAX_MATERIALIZED_ELEMENTS})"
            )

        step = -1 if start > end else 1
        indexes: list[int | None] = [start]

        if start < 0 or start >= length:
            # Return empty result
            return [] if isinstance(_container, list) else {}

        while start != end:
            start = start + step
            if start < 0 or start >= length:
                indexes.append(None)
            else:
                indexes.append(start)

        if isinstance(_container, list):
            result: list = []
            for i in indexes:
                if i is None:
                    result.append(None)
                else:
                    result.append(_container[i])
            return result
        else:
            keys = list(_container.keys())
            result_dict: dict = {}
            for i in indexes:
                if i is not None:
                    k = keys[i]
                    result_dict[k] = _container[k]
            return result_dict

    @WordDecorator("( container:any n:number [options:WordOptions] -- result:any )", "Take first n elements (record in -> record out, insertion order)")
    async def TAKE(self, container: Any, n: int, options: dict[str, Any]) -> Any:
        interp = self._module.interp
        assert interp is not None

        flags = {
            "with_key": options.get("with_key"),
            "push_rest": options.get("push_rest"),
        }

        if container is None:
            container = []

        taken: Any
        rest: Any
        if isinstance(container, list):
            taken = container[:n]
            rest = container[n:]
        else:
            # Records keep their shape and insertion order
            keys = list(container.keys())
            taken = {k: container[k] for k in keys[:n]}
            rest = {k: container[k] for k in keys[n:]}

        if flags["push_rest"]:
            interp.stack_push(taken)
            return rest

        return taken

    @WordDecorator("( container:any n:number -- result:any )", "Skip first n elements from array or record")
    async def SKIP(self, container: Any, n: int) -> Any:
        if container is None:
            return []
        if n <= 0:
            return container

        if isinstance(container, list):
            return container[n:]
        else:
            # Records keep their shape and insertion order
            keys = list(container.keys())
            return {k: container[k] for k in keys[n:]}

    @WordDecorator(
        "( container:any n:number -- result:any )",
        "Take last n elements from array or record (insertion order for records).",
        "TAKE-LAST",
    )
    async def TAKE_LAST(self, container: Any, n: int) -> Any:
        if container is None:
            return []
        if n <= 0:
            return [] if isinstance(container, list) else {}

        if isinstance(container, list):
            return container[max(0, len(container) - n):]
        keys = list(container.keys())
        tail = keys[max(0, len(keys) - n):]
        return {k: container[k] for k in tail}

    @ForthicDirectWord("( container:any value:any -- key:any )", "Find key of value in container", "KEY-OF")
    async def KEY_OF(self, interp: Interpreter) -> None:
        value = interp.stack_pop()
        container = interp.stack_pop()

        if container is None:
            interp.stack_push(None)
            return

        if isinstance(container, list):
            try:
                index = container.index(value)
                interp.stack_push(index)
            except ValueError:
                interp.stack_push(None)
        else:
            for key in container.keys():
                if container[key] == value:
                    interp.stack_push(key)
                    return
            interp.stack_push(None)

    # ==================
    # Transform
    # ==================

    @ForthicDirectWord(
        "( items:any forthic:string [options:WordOptions] -- mapped:any )",
        "Map function over items. Options: with_key (bool), depth (num), outcomes (bool). "
        "With outcomes, each element maps to {ok: value} or {error: {message, error_type}} — "
        "per-element failures don't abort and can't disturb the stack (MAP restores its own "
        "pushes). Example: [1 2 3] '2 *' [.outcomes TRUE] ~> MAP",
    )
    async def MAP(self, interp: Interpreter) -> None:
        options_dict = {}
        from ...word_options import WordOptions

        if len(interp.get_stack()) > 0:
            top = interp.stack_peek()
            if isinstance(top, WordOptions):
                opts = interp.stack_pop()
                options_dict = opts.to_dict()

        forthic = interp.stack_pop()
        items = interp.stack_pop()

        flags = {
            "with_key": options_dict.get("with_key", False),
            "depth": options_dict.get("depth", 0),
            "outcomes": options_dict.get("outcomes", False),
        }

        string_location = interp.get_string_location()

        if items is None or len(items) == 0:
            interp.stack_push(items)
            return

        result = await self._map_items(interp, items, forthic, string_location, flags)
        interp.stack_push(result)

    async def _map_items(
        self, interp: Interpreter, items: Any, forthic: str, forthic_location: Any, flags: dict
    ) -> Any:
        """Map forthic over items with optional recursion depth."""

        async def map_value(key: str | int, value: Any) -> Any:
            # Errors propagate (Forthic's default) unless outcomes mode is
            # on, in which case each element maps to {ok: value} /
            # {error: info}. The snapshot is taken BEFORE the item is pushed
            # — MAP owns that push, so a failed element consumes the item
            # and cannot strand it (this is why outcomes lives on MAP rather
            # than being composed from TRY, whose snapshot would include the
            # pushed item and faithfully restore it).
            if not flags["outcomes"]:
                if flags["with_key"]:
                    interp.stack_push(key)
                interp.stack_push(value)
                await interp.run(forthic, forthic_location)
                return interp.stack_pop()

            snapshot = list(interp.get_stack().get_raw_items())
            module_depth = interp.module_stack_depth()
            if flags["with_key"]:
                interp.stack_push(key)
            interp.stack_push(value)
            return await run_to_outcome(
                interp, forthic, forthic_location, snapshot, module_depth
            )

        async def descend_record(record: dict, depth: int, accum: dict) -> dict:
            for k in record.keys():
                item = record[k]
                if depth > 0 and isinstance(item, list):
                    accum[k] = []
                    await descend_list(item, depth - 1, accum[k])
                elif depth > 0 and isinstance(item, dict):
                    accum[k] = {}
                    await descend_record(item, depth - 1, accum[k])
                else:
                    # Scalar leaf (or depth exhausted): map it
                    accum[k] = await map_value(k, item)
            return accum

        async def descend_list(items_list: list, depth: int, accum: list) -> list:
            for i, item in enumerate(items_list):
                if depth > 0 and isinstance(item, list):
                    accum.append([])
                    await descend_list(item, depth - 1, accum[-1])
                elif depth > 0 and isinstance(item, dict):
                    accum.append({})
                    await descend_record(item, depth - 1, accum[-1])
                else:
                    # Scalar leaf (or depth exhausted): map it
                    accum.append(await map_value(i, item))
            return accum

        depth = flags["depth"]

        if isinstance(items, list):
            result: list | dict = await descend_list(items, depth, [])
        else:
            result = await descend_record(items, depth, {})

        return result

    @WordDecorator("( container:any -- container:any )", "Reverse array")
    async def REVERSE(self, container: Any) -> Any:
        if container is None:
            return container

        if isinstance(container, list):
            return list(reversed(container))

        return container

    @ForthicDirectWord("( container:any -- elements:any )", "Unpack array or record elements onto stack")
    async def UNPACK(self, interp: Interpreter) -> None:
        container = interp.stack_pop()

        if container is None:
            container = []

        if isinstance(container, list):
            for item in container:
                interp.stack_push(item)
        else:
            for k in container.keys():
                interp.stack_push(container[k])

    # ==================
    # Combine
    # ==================

    @WordDecorator("( array:any[] item:any -- array:any[] )", "Append item to array. For records, use JQ! to set a key.")
    async def APPEND(self, container: Any, item: Any) -> Any:
        result = container if container is not None else []

        if not isinstance(result, list):
            raise ValueError("APPEND requires an array. For records, use JQ! to set a key.")

        # Copy first: append() mutates in place, which would alias the input
        return [*result, item]

    @WordDecorator("( container1:any[] container2:any[] -- result:any[] )", "Zip two arrays into array of pairs")
    async def ZIP(self, container1: list, container2: list) -> Any:
        if container1 is None:
            container1 = []
        if container2 is None:
            container2 = []

        if isinstance(container2, list):
            result = []
            for i in range(len(container1)):
                value2 = container2[i] if i < len(container2) else None
                result.append([container1[i], value2])
        else:
            result = {}
            for k in container1.keys():
                v = container1[k]
                result[k] = [v, container2.get(k)]

        return result

    @WordDecorator(
        "( container1:any[] container2:any[] forthic:string -- result:any[] )",
        "Zip two arrays with combining function",
        "ZIP-WITH",
    )
    async def ZIP_WITH(self, container1: list, container2: list, forthic: str) -> Any:
        interp = self._module.interp
        assert interp is not None
        string_location = interp.get_string_location()

        if container1 is None:
            container1 = []
        if container2 is None:
            container2 = []

        if isinstance(container2, list):
            result = []
            for i in range(len(container1)):
                value2 = container2[i] if i < len(container2) else None
                interp.stack_push(container1[i])
                interp.stack_push(value2)
                await interp.run(forthic, string_location)
                res = interp.stack_pop()
                result.append(res)
        else:
            result = {}
            keys = list(container1.keys())
            for k in keys:
                interp.stack_push(container1[k])
                interp.stack_push(container2.get(k))
                await interp.run(forthic, string_location)
                res = interp.stack_pop()
                result[k] = res

        return result

    # ==================
    # Filter
    # ==================

    @ForthicDirectWord(
        "( container:any forthic:string [options:WordOptions] -- filtered:any )",
        "Keep items where the predicate returns truthy. Options: with_key (bool). Records keep their shape and insertion order.",
        "FILTER",
    )
    async def FILTER(self, interp: Interpreter) -> None:
        options_dict = {}
        from ...word_options import WordOptions

        if len(interp.get_stack()) > 0:
            top = interp.stack_peek()
            if isinstance(top, WordOptions):
                opts = interp.stack_pop()
                options_dict = opts.to_dict()

        forthic = interp.stack_pop()
        container = interp.stack_pop()

        flags = {
            "with_key": options_dict.get("with_key"),
        }

        string_location = interp.get_string_location()

        if container is None:
            interp.stack_push(container)
            return

        if isinstance(container, list):
            result: Any = []
            for i, item in enumerate(container):
                if flags["with_key"]:
                    interp.stack_push(i)
                interp.stack_push(item)
                await interp.run(forthic, string_location)
                should_select = interp.stack_pop()
                if is_truthy(should_select):
                    result.append(item)
        else:
            result = {}
            for k in container.keys():
                v = container[k]
                if flags["with_key"]:
                    interp.stack_push(k)
                interp.stack_push(v)
                await interp.run(forthic, string_location)
                should_select = interp.stack_pop()
                if is_truthy(should_select):
                    result[k] = v

        interp.stack_push(result)

    @WordDecorator("( array:any[] -- array:any[] )", "Remove duplicates from array (structural equality; keeps first occurrence)")
    async def UNIQUE(self, array: Any) -> Any:
        if not isinstance(array, list):
            return array
        # Structural dedupe via compact JSON keys (dict.fromkeys raised on
        # unhashable elements like records) — same policy as UNIQUE-BY/SORT-U
        seen = set()
        result = []
        for item in array:
            key = to_compact_json(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    @staticmethod
    def _set_op(lcontainer: Any, rcontainer: Any, keep: bool) -> Any:
        """Shared set operation for DIFFERENCE (keep=False) and INTERSECTION
        (keep=True). The result follows the LEFT operand's shape:
        - array left: element membership against the right's elements (its
          values if the right is a record);
        - record left: keep/drop entries whose KEY is in the right's key set
          (its elements if the right is an array, its keys if it's a record)
          — i.e. INTERSECTION behaves like PICK and DIFFERENCE like OMIT.
        """
        left = lcontainer if lcontainer is not None else []
        right = rcontainer if rcontainer is not None else []

        if isinstance(left, list):
            relements = right if isinstance(right, list) else list(right.values())
            return [
                item
                for item in left
                if any(values_equal(item, el) for el in relements) == keep
            ]

        rkeys = set(right) if isinstance(right, list) else set(right.keys())
        return {k: v for k, v in left.items() if (k in rkeys) == keep}

    @WordDecorator("( lcontainer:any rcontainer:any -- result:any )", "Set difference between two containers")
    async def DIFFERENCE(self, lcontainer: Any, rcontainer: Any) -> Any:
        return ArrayModule._set_op(lcontainer, rcontainer, False)

    @WordDecorator("( lcontainer:any rcontainer:any -- result:any )", "Set intersection between two containers")
    async def INTERSECTION(self, lcontainer: Any, rcontainer: Any) -> Any:
        return ArrayModule._set_op(lcontainer, rcontainer, True)

    @WordDecorator("( lcontainer:any rcontainer:any -- result:any )", "Set union between two containers")
    async def UNION(self, lcontainer: Any, rcontainer: Any) -> Any:
        if lcontainer is None:
            lcontainer = []
        if rcontainer is None:
            rcontainer = []

        def union(left: list, right: list) -> list:
            keyset: dict = {}
            for item in left:
                keyset[item] = True
            for item in right:
                keyset[item] = True
            return list(keyset.keys())

        if isinstance(rcontainer, list):
            result: list | dict = union(lcontainer, rcontainer)
        else:
            lkeys = list(lcontainer.keys())
            rkeys = list(rcontainer.keys())

            keys = union(lkeys, rkeys)
            result = {}
            for k in keys:
                val = lcontainer.get(k)
                if val is None:
                    val = rcontainer.get(k)
                result[k] = val

        return result

    @ForthicDirectWord(
        "( items:any forthic:string -- item:any )",
        "Return the first item where forthic returns truthy, or null if none (short-circuits).",
        "FIND",
    )
    async def FIND(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        items = interp.stack_pop()
        if not items:
            interp.stack_push(None)
            return
        string_location = interp.get_string_location()
        seq = items if isinstance(items, list) else list(items.values())
        for item in seq:
            interp.stack_push(item)
            await interp.run(forthic, string_location)
            if is_truthy(interp.stack_pop()):
                interp.stack_push(item)
                return
        interp.stack_push(None)

    @ForthicDirectWord(
        "( items:any forthic:string -- n:number )",
        "Count items where forthic returns truthy.",
        "COUNT",
    )
    async def COUNT(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        items = interp.stack_pop()
        if not items:
            interp.stack_push(0)
            return
        string_location = interp.get_string_location()
        seq = items if isinstance(items, list) else list(items.values())
        n = 0
        for item in seq:
            interp.stack_push(item)
            await interp.run(forthic, string_location)
            if is_truthy(interp.stack_pop()):
                n += 1
        interp.stack_push(n)

    @ForthicDirectWord(
        "( items:any[] forthic:string -- sorted:any[] )",
        "Sort items by the value forthic produces (ascending, stable).",
        "SORT-BY",
    )
    async def SORT_BY(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        items = interp.stack_pop()
        if not isinstance(items, list):
            interp.stack_push(items)
            return
        string_location = interp.get_string_location()
        decorated = []
        for item in items:
            interp.stack_push(item)
            await interp.run(forthic, string_location)
            decorated.append((item, interp.stack_pop()))
        # Python's sort is stable: equal keys keep input order
        from functools import cmp_to_key

        def cmp(a: tuple, b: tuple) -> int:
            if a[1] is None or b[1] is None:
                return 0 if a[1] is b[1] else (1 if a[1] is None else -1)
            if a[1] < b[1]:
                return -1
            if a[1] > b[1]:
                return 1
            return 0

        decorated.sort(key=cmp_to_key(cmp))
        interp.stack_push([d[0] for d in decorated])

    @ForthicDirectWord(
        "( items:any[] forthic:string -- item:any )",
        "Return the item with the smallest value produced by forthic. Null on empty input; ties keep the earliest item.",
        "MIN-BY",
    )
    async def MIN_BY(self, interp: Interpreter) -> None:
        await self._best_by(interp, lambda key, best: key < best)

    @ForthicDirectWord(
        "( items:any[] forthic:string -- item:any )",
        "Return the item with the largest value produced by forthic. Null on empty input; ties keep the earliest item.",
        "MAX-BY",
    )
    async def MAX_BY(self, interp: Interpreter) -> None:
        await self._best_by(interp, lambda key, best: key > best)

    async def _best_by(self, interp: Interpreter, wins: Any) -> None:
        forthic = interp.stack_pop()
        items = interp.stack_pop()
        if not isinstance(items, list) or len(items) == 0:
            interp.stack_push(None)
            return
        string_location = interp.get_string_location()
        best_item = None
        best_key = None
        first = True
        for item in items:
            interp.stack_push(item)
            await interp.run(forthic, string_location)
            key = interp.stack_pop()
            if first or wins(key, best_key):
                best_item = item
                best_key = key
                first = False
        interp.stack_push(best_item)

    @ForthicDirectWord(
        "( items:any[] forthic:string -- items:any[] )",
        "Dedupe items by the key forthic produces (keeps first occurrence).",
        "UNIQUE-BY",
    )
    async def UNIQUE_BY(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        items = interp.stack_pop()
        if not isinstance(items, list):
            interp.stack_push(items)
            return
        string_location = interp.get_string_location()
        seen = set()
        result = []
        for item in items:
            interp.stack_push(item)
            await interp.run(forthic, string_location)
            skey = to_compact_json(interp.stack_pop())
            if skey not in seen:
                seen.add(skey)
                result.append(item)
        interp.stack_push(result)

    @WordDecorator(
        "( strings:any[] -- strings:any[] )",
        "Sort an array and remove duplicates (bash sort -u).",
        "SORT-U",
    )
    async def SORT_U(self, strings: Any) -> Any:
        if not isinstance(strings, list):
            return strings
        non_null = sorted(x for x in strings if x is not None)
        ordered = non_null + [x for x in strings if x is None]
        seen = set()
        result = []
        for item in ordered:
            key = to_compact_json(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    @WordDecorator(
        "( items:any[] -- pairs:any[] )",
        "Pair each item with its index: [v0 v1 v2] -> [[0 v0] [1 v1] [2 v2]]. Non-arrays yield an empty array.",
        "NUMBERED",
    )
    async def NUMBERED(self, items: Any) -> list:
        if not isinstance(items, list):
            return []
        return [[i, item] for i, item in enumerate(items)]

    @ForthicDirectWord(
        "( container:any key:any|any[] forthic:string -- container:any )",
        "Apply forthic to the value at key/index, returning a new container with that slot transformed. "
        "The key arg may be a single key (one-level update) or a path-array for deep updates. "
        "Misses (missing key, out-of-range index, scalar mid-path) are silent no-ops. "
        "Polymorphic over arrays and records. Equivalent of jq's |= operator.",
        "MAP-AT",
    )
    async def MAP_AT(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        key = interp.stack_pop()
        container = interp.stack_pop()
        if container is None:
            interp.stack_push(container)
            return
        string_location = interp.get_string_location()

        async def apply(value: Any) -> Any:
            interp.stack_push(value)
            await interp.run(forthic, string_location)
            return interp.stack_pop()

        async def map_at_single(cont: Any, k: Any) -> Any:
            if isinstance(cont, list):
                idx = k if isinstance(k, int) and not isinstance(k, bool) else _as_index(k)
                if idx is None or idx < 0 or idx >= len(cont):
                    return cont
                result = list(cont)
                result[idx] = await apply(result[idx])
                return result
            if isinstance(cont, dict):
                if k not in cont:
                    return cont
                result_rec = dict(cont)
                result_rec[k] = await apply(result_rec[k])
                return result_rec
            return cont

        async def map_at_path(cont: Any, head: Any, rest: list) -> Any:
            if not rest:
                return await map_at_single(cont, head)
            if isinstance(cont, list):
                idx = head if isinstance(head, int) and not isinstance(head, bool) else _as_index(head)
                if idx is None or idx < 0 or idx >= len(cont):
                    return cont
                result = list(cont)
                result[idx] = await map_at_path(result[idx], rest[0], rest[1:])
                return result
            if isinstance(cont, dict):
                if head not in cont:
                    return cont
                result_rec = dict(cont)
                result_rec[head] = await map_at_path(result_rec[head], rest[0], rest[1:])
                return result_rec
            return cont

        if isinstance(key, list):
            if len(key) == 0:
                interp.stack_push(await apply(container))
                return
            interp.stack_push(await map_at_path(container, key[0], key[1:]))
            return
        interp.stack_push(await map_at_single(container, key))

    # ==================
    # Sort
    # ==================

    @WordDecorator(
        "( container:any[] [options:WordOptions] -- array:any[] )",
        'Sort container. Options: comparator (string or function). Example: [3 1 4] [.comparator "-1 *"] ~> SORT',
    )
    async def SORT(self, container: list, options: dict[str, Any]) -> list:
        if container is None:
            return container
        if not isinstance(container, list):
            return container

        interp = self._module.interp
        assert interp is not None
        comparator = options.get("comparator")

        flag_string_position = interp.get_string_location()

        # Default sort
        def sort_without_comparator() -> list:
            # Filter out None values and sort them separately
            non_null = [x for x in container if x is not None]
            null_values = [x for x in container if x is None]
            return sorted(non_null) + null_values

        # Sort using a forthic string as a key function
        async def sort_with_key_forthic(forthic: str) -> list:
            async def make_aug_array(vals: list) -> list:
                res = []
                for val in vals:
                    interp.stack_push(val)
                    await interp.run(forthic, flag_string_position)
                    aug_val = interp.stack_pop()
                    res.append([val, aug_val])
                return res

            def cmp_items(left: tuple, right: tuple) -> int:
                l_val = left[1]
                r_val = right[1]

                if l_val < r_val:
                    return -1
                elif l_val > r_val:
                    return 1
                else:
                    return 0

            def de_aug_array(aug_vals: list) -> list:
                return [aug_val[0] for aug_val in aug_vals]

            # Create augmented array, sort it, return underlying values
            aug_array = await make_aug_array(container)
            from functools import cmp_to_key

            aug_array.sort(key=cmp_to_key(cmp_items))
            return de_aug_array(aug_array)

        # Sort with key func
        def sort_with_key_func(key_func: Any) -> list:
            def cmp_items(left: Any, right: Any) -> int:
                l_val = key_func(left)
                r_val = key_func(right)
                if l_val < r_val:
                    return -1
                elif l_val > r_val:
                    return 1
                else:
                    return 0

            from functools import cmp_to_key

            result_copy = container.copy()
            result_copy.sort(key=cmp_to_key(cmp_items))
            return result_copy

        # Figure out what to do
        if isinstance(comparator, str):
            result = await sort_with_key_forthic(comparator)
        elif comparator is None:
            result = sort_without_comparator()
        else:
            result = sort_with_key_func(comparator)

        return result

    @WordDecorator("( items:any[] forthic:string -- indexed:any )", "Create index mapping from array indices to values")
    async def INDEX(self, items: list, forthic: str) -> dict:
        interp = self._module.interp
        assert interp is not None
        string_location = interp.get_string_location()

        if items is None:
            return None

        result: dict = {}
        for item in items:
            interp.stack_push(item)
            await interp.run(forthic, string_location)
            keys = interp.stack_pop()
            for k in keys:
                lowercased_key = k.lower()
                if lowercased_key in result:
                    result[lowercased_key].append(item)
                else:
                    result[lowercased_key] = [item]

        return result

    @WordDecorator("( container:any[] field:string -- indexed:any )", "Index records by field value", "BY-FIELD")
    async def BY_FIELD(self, container: list, field: str) -> dict:
        if container is None:
            container = []

        if isinstance(container, list):
            values = container
        else:
            values = []
            for k in container.keys():
                values.append(container[k])

        result: dict = {}
        for v in values:
            # Falsy records are skipped; last occurrence of a key wins.
            # Missing fields group under "null" (cross-runtime contract)
            if is_truthy(v):
                result[value_to_key_string(v.get(field))] = v

        return result

    @WordDecorator("( container:any[] field:string -- grouped:any )", "Group records by field value", "GROUP-BY-FIELD")
    async def GROUP_BY_FIELD(self, container: list, field: str) -> dict:
        if container is None:
            container = []

        if isinstance(container, list):
            values = container
        else:
            values = [container[k] for k in container.keys()]

        result: dict = {}
        for v in values:
            if v is None:
                # A proper error instead of the raw TypeError None[field]
                # raises; matches the ts/rs message
                raise ValueError(f"GROUP-BY-FIELD: cannot read field '{field}' of NULL")
            # Missing fields group under "null" (cross-runtime contract);
            # array-valued fields put the record in every group it names
            field_val = v.get(field)
            if isinstance(field_val, list):
                for fv in field_val:
                    key = value_to_key_string(fv)
                    result.setdefault(key, []).append(v)
            else:
                key = value_to_key_string(field_val)
                result.setdefault(key, []).append(v)

        return result

    @ForthicDirectWord(
        "( items:any forthic:string [options:WordOptions] -- grouped:any )",
        "Group items by function result. Options: with_key (bool)",
        "GROUP-BY",
    )
    async def GROUP_BY(self, interp: Interpreter) -> None:
        options_dict = {}
        from ...word_options import WordOptions

        if len(interp.get_stack()) > 0:
            top = interp.stack_peek()
            if isinstance(top, WordOptions):
                opts = interp.stack_pop()
                options_dict = opts.to_dict()

        forthic = interp.stack_pop()
        items = interp.stack_pop()

        if items is None:
            items = []

        string_location = interp.get_string_location()
        with_key = options_dict.get("with_key")

        result: dict = {}

        async def process_item(item: Any, key: Any = None) -> None:
            if with_key:
                interp.stack_push(key)
            interp.stack_push(item)
            await interp.run(forthic, string_location)
            # Group keys coerce like JS object keys (strings in every runtime)
            group_key = value_to_key_string(interp.stack_pop())
            result.setdefault(group_key, []).append(item)

        if isinstance(items, list):
            for i, item in enumerate(items):
                await process_item(item, i)
        else:
            for key in items.keys():
                await process_item(items[key], key)

        interp.stack_push(result)

    @WordDecorator("( container:any[] n:number -- groups:any[] )", "Split array into groups of size n", "GROUPS-OF")
    async def GROUPS_OF(self, container: list, n: int) -> list:
        n = int(n)  # fractional group sizes truncate (sanctioned rs precedent)
        if n <= 0:
            raise ValueError("GROUPS-OF requires group size > 0")

        if container is None:
            container = []

        def group_items(items: list, group_size: int) -> list:
            num_groups = (len(items) + group_size - 1) // group_size  # Ceiling division
            res = []
            remaining = items.copy()
            for _ in range(num_groups):
                res.append(remaining[:group_size])
                remaining = remaining[group_size:]
            return res

        def extract_rec(record: dict, keys: list) -> dict:
            res = {}
            for k in keys:
                res[k] = record[k]
            return res

        if isinstance(container, list):
            result = group_items(container, n)
        else:
            keys = list(container.keys())
            key_groups = group_items(keys, n)
            result = [extract_rec(container, ks) for ks in key_groups]

        return result

    # ==================
    # Utility
    # ==================

    @ForthicDirectWord(
        "( items:any forthic:string [options:WordOptions] -- ? )",
        "Execute forthic for each item. Options: with_key (bool). "
        "For error tolerance compose with TRY: items \"'PROCESS' TRY\" FOREACH",
    )
    async def FOREACH(self, interp: Interpreter) -> None:
        options_dict = {}
        from ...word_options import WordOptions

        if len(interp.get_stack()) > 0:
            top = interp.stack_peek()
            if isinstance(top, WordOptions):
                opts = interp.stack_pop()
                options_dict = opts.to_dict()

        forthic = interp.stack_pop()
        items = interp.stack_pop()

        if items is None:
            items = []

        string_location = interp.get_string_location()

        with_key = options_dict.get("with_key")

        if isinstance(items, list):
            for i, item in enumerate(items):
                if with_key:
                    interp.stack_push(i)
                interp.stack_push(item)
                await interp.run(forthic, string_location)
        else:
            for k in items.keys():
                item = items[k]
                if with_key:
                    interp.stack_push(k)
                interp.stack_push(item)
                await interp.run(forthic, string_location)

    @ForthicDirectWord("( container:any initial:any forthic:string -- result:any )", "Reduce array or record with accumulator")
    async def REDUCE(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        initial = interp.stack_pop()
        container = interp.stack_pop()

        if container is None:
            container = []

        string_location = interp.get_string_location()

        interp.stack_push(initial)

        if isinstance(container, list):
            for item in container:
                interp.stack_push(item)
                await interp.run(forthic, string_location)
        else:
            for k in container.keys():
                v = container[k]
                interp.stack_push(v)
                await interp.run(forthic, string_location)

        result = interp.stack_pop()
        interp.stack_push(result)

    @WordDecorator(
        "( container:any [options:WordOptions] -- flat:any )",
        "Flatten nested arrays or records. Options: depth (number). Example: [[[1 2]]] [.depth 1] ~> FLATTEN",
    )
    async def FLATTEN(self, container: Any, options: dict[str, Any]) -> Any:
        if container is None:
            return []

        depth = options.get("depth")

        def fully_flatten_array(items: list, accum: list) -> list:
            for item in items:
                if isinstance(item, list):
                    fully_flatten_array(item, accum)
                else:
                    accum.append(item)
            return accum

        def flatten_array(items: list, d: int | None, accum: list) -> list:
            if d is None:
                return fully_flatten_array(items, accum)

            for item in items:
                if d > 0 and isinstance(item, list):
                    flatten_array(item, d - 1, accum)
                else:
                    accum.append(item)
            return accum

        def is_record(obj: Any) -> bool:
            if not isinstance(obj, dict):
                return False
            return len(obj.keys()) > 0

        def add_to_record_result(item: Any, key: str, keys: list, result: dict) -> None:
            new_key = "\t".join(keys + [key])
            result[new_key] = item

        def fully_flatten_record(record: dict, res: dict, keys: list) -> dict:
            for k in record.keys():
                item = record[k]
                if is_record(item):
                    fully_flatten_record(item, res, keys + [k])
                else:
                    add_to_record_result(item, k, keys, res)
            return res

        def flatten_record(record: dict, d: int | None, res: dict, keys: list) -> dict:
            if d is None:
                return fully_flatten_record(record, res, keys)

            for k in record.keys():
                item = record[k]
                if d > 0 and is_record(item):
                    flatten_record(item, d - 1, res, keys + [k])
                else:
                    add_to_record_result(item, k, keys, res)
            return res

        if isinstance(container, list):
            result: list | dict = flatten_array(container, depth, [])
        else:
            result = flatten_record(container, depth, {}, [])

        return result

    @ForthicDirectWord(
        "( num_times:number forthic:string -- )",
        "Run forthic num_times. Each invocation runs in the current stack — no automatic per-iteration value passing. (Classic <REPEAT dropped: it pushed item+result each pass.)",
        "TIMES-RUN",
    )
    async def TIMES_RUN(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        num_times = interp.stack_pop()
        if num_times is None or not forthic:
            return
        string_location = interp.get_string_location()
        for _ in range(int(num_times)):
            await interp.run(forthic, string_location)
