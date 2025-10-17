"""Array module - Array and collection operations.

Provides array manipulation including mapping, filtering, and grouping.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...interpreter import Interpreter

from ...decorators import DecoratedModule, DirectWord, register_module_doc
from ...decorators import Word as WordDecorator


class ArrayModule(DecoratedModule):
    """Array and collection operations for manipulating arrays and records."""

    def __init__(self):
        super().__init__("array")
        register_module_doc(
            ArrayModule,
            """
Array and collection operations for manipulating arrays and records.

## Categories
- Access: NTH, LAST, SLICE, TAKE, DROP, LENGTH, INDEX, KEY-OF
- Transform: MAP, REVERSE
- Combine: APPEND, ZIP, ZIP_WITH, CONCAT
- Filter: SELECT, UNIQUE, DIFFERENCE, INTERSECTION, UNION
- Sort: SORT, SHUFFLE, ROTATE
- Group: BY_FIELD, GROUP_BY_FIELD, GROUP_BY, GROUPS_OF
- Utility: <REPEAT, FOREACH, REDUCE, UNPACK, FLATTEN

## Options
Several words support options via the ~> operator using syntax: [.option_name value ...] ~> WORD
- with_key: Push index/key before value (MAP, FOREACH, GROUP_BY, SELECT)
- push_error: Push error array after execution (MAP, FOREACH)
- depth: Recursion depth for nested operations (MAP, FLATTEN)
- push_rest: Push remaining items after operation (MAP, TAKE)
- comparator: Custom comparison function as Forthic string (SORT)

## Examples
[10 20 30] '2 *' MAP
[10 20 30] '+ 2 *' [.with_key TRUE] ~> MAP
[[[1 2]] [[3 4]]] [.depth 1] ~> FLATTEN
[3 1 4 1 5] [.comparator "-1 *"] ~> SORT
[.with_key TRUE .push_error TRUE] ~> MAP
            """,
        )

    # ==================
    # Access
    # ==================

    @WordDecorator("( container:any -- length:number )", "Get length of array or record")
    async def LENGTH(self, container: Any) -> int:
        if container is None:
            return 0
        if isinstance(container, list):
            return len(container)
        if isinstance(container, dict):
            return len(container.keys())
        if isinstance(container, str):
            return len(container)
        return 0

    @DirectWord("( container:any n:number -- item:any )", "Get nth element from array or record")
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
            keys = sorted(container.keys())
            if n < 0 or n >= len(keys):
                interp.stack_push(None)
            else:
                key = keys[n]
                interp.stack_push(container[key])

    @WordDecorator("( container:any -- item:any )", "Get last element from array or record")
    async def LAST(self, container: Any) -> Any:
        if container is None:
            return None

        if isinstance(container, list):
            if len(container) == 0:
                return None
            return container[-1]
        else:
            keys = sorted(container.keys())
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
            keys = sorted(_container.keys())
            result_dict: dict = {}
            for i in indexes:
                if i is not None:
                    k = keys[i]
                    result_dict[k] = _container[k]
            return result_dict

    @WordDecorator("( container:any[] n:number [options:WordOptions] -- result:any[] )", "Take first n elements")
    async def TAKE(self, container: list, n: int, options: dict[str, Any]) -> list:
        interp = self._module.interp

        flags = {
            "with_key": options.get("with_key"),
            "push_rest": options.get("push_rest"),
        }

        if container is None:
            container = []

        if isinstance(container, list):
            taken = container[:n]
            rest = container[n:]
        else:
            keys = sorted(container.keys())
            taken_keys = keys[:n]
            rest_keys = keys[n:]
            taken = [container[k] for k in taken_keys]
            rest = [container[k] for k in rest_keys]

        if flags["push_rest"]:
            interp.stack_push(taken)
            return rest

        return taken

    @WordDecorator("( container:any n:number -- result:any )", "Drop first n elements from array or record")
    async def DROP(self, container: Any, n: int) -> Any:
        if container is None:
            return []
        if n <= 0:
            return container

        if isinstance(container, list):
            return container[n:]
        else:
            keys = sorted(container.keys())
            rest_keys = keys[n:]
            return [container[k] for k in rest_keys]

    @DirectWord("( container:any value:any -- key:any )", "Find key of value in container")
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

    @DirectWord(
        "( items:any forthic:string [options:WordOptions] -- mapped:any )",
        "Map function over items. Options: with_key (bool), push_error (bool), depth (num), push_rest (bool)",
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
            "push_error": options_dict.get("push_error", False),
            "depth": options_dict.get("depth", 0),
            "push_rest": options_dict.get("push_rest", False),
        }

        string_location = interp.get_string_location()

        if items is None or len(items) == 0:
            interp.stack_push(items)
            return

        result_data = await self._map_items(interp, items, forthic, string_location, flags)
        result = result_data[0]
        errors = result_data[1]

        interp.stack_push(result)
        if flags["push_error"]:
            interp.stack_push(errors)

    async def _map_items(
        self, interp: Interpreter, items: Any, forthic: str, forthic_location: Any, flags: dict
    ) -> tuple[Any, list]:
        """Map forthic over items with optional recursion depth."""

        async def map_value(key: str | int, value: Any, errors: list) -> Any:
            if flags["with_key"]:
                interp.stack_push(key)
            interp.stack_push(value)

            if flags["push_error"]:
                error = None
                try:
                    await interp.run(forthic, forthic_location)
                except Exception as e:
                    interp.stack_push(None)
                    error = e
                errors.append(error)
            else:
                await interp.run(forthic, forthic_location)

            return interp.stack_pop()

        async def descend_record(record: dict, depth: int, accum: dict, errors: list) -> dict:
            for k in record.keys():
                item = record[k]
                if depth > 0:
                    if isinstance(item, list):
                        accum[k] = []
                        await descend_list(item, depth - 1, accum[k], errors)
                    else:
                        accum[k] = {}
                        await descend_record(item, depth - 1, accum[k], errors)
                else:
                    accum[k] = await map_value(k, item, errors)
            return accum

        async def descend_list(items_list: list, depth: int, accum: list, errors: list) -> list:
            for i, item in enumerate(items_list):
                if depth > 0:
                    if isinstance(item, list):
                        accum.append([])
                        await descend_list(item, depth - 1, accum[-1], errors)
                    else:
                        accum.append({})
                        await descend_record(item, depth - 1, accum[-1], errors)
                else:
                    accum.append(await map_value(i, item, errors))
            return accum

        errors: list = []
        depth = flags["depth"]

        if isinstance(items, list):
            result = await descend_list(items, depth, [], errors)
        else:
            result = await descend_record(items, depth, {}, errors)

        return (result, errors)

    @WordDecorator("( container:any -- container:any )", "Reverse array")
    async def REVERSE(self, container: Any) -> Any:
        if container is None:
            return container

        if isinstance(container, list):
            return list(reversed(container))

        return container

    @WordDecorator("( container:any -- container:any )", "Rotate container by moving last element to front")
    async def ROTATE(self, container: Any) -> Any:
        if container is None:
            return container

        if isinstance(container, list):
            if len(container) > 0:
                result = container.copy()
                val = result.pop()
                result.insert(0, val)
                return result

        return container

    @DirectWord("( container:any -- elements:any )", "Unpack array or record elements onto stack")
    async def UNPACK(self, interp: Interpreter) -> None:
        container = interp.stack_pop()

        if container is None:
            container = []

        if isinstance(container, list):
            for item in container:
                interp.stack_push(item)
        else:
            keys = sorted(container.keys())
            for k in keys:
                interp.stack_push(container[k])

    # ==================
    # Combine
    # ==================

    @WordDecorator("( container:any item:any -- container:any )", "Append item to array or add key-value to record")
    async def APPEND(self, container: Any, item: Any) -> Any:
        result = container if container is not None else []

        if isinstance(result, list):
            result.append(item)
        else:
            # If not a list, treat as record - item should be [key, value]
            result[item[0]] = item[1]

        return result

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
        "( container1:any[] container2:any[] forthic:string -- result:any[] )", "Zip two arrays with combining function"
    )
    async def ZIP_WITH(self, container1: list, container2: list, forthic: str) -> Any:
        interp = self._module.interp
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

    @DirectWord(
        "( container:any forthic:string [options:WordOptions] -- filtered:any )",
        "Filter items with predicate. Options: with_key (bool)",
    )
    async def SELECT(self, interp: Interpreter) -> None:
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
            result = []
            for i, item in enumerate(container):
                if flags["with_key"]:
                    interp.stack_push(i)
                interp.stack_push(item)
                await interp.run(forthic, string_location)
                should_select = interp.stack_pop()
                if should_select:
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
                if should_select:
                    result[k] = v

        interp.stack_push(result)

    @WordDecorator("( array:any[] -- array:any[] )", "Remove duplicates from array")
    async def UNIQUE(self, array: list) -> list:
        if array is None:
            return array

        if isinstance(array, list):
            result = list(dict.fromkeys(array))  # Preserves order in Python 3.7+
            return result

        return array

    @WordDecorator("( lcontainer:any rcontainer:any -- result:any )", "Set difference between two containers")
    async def DIFFERENCE(self, lcontainer: Any, rcontainer: Any) -> Any:
        _lcontainer = lcontainer if lcontainer is not None else []
        _rcontainer = rcontainer if rcontainer is not None else []

        def difference(l: list, r: list) -> list:
            res = []
            for item in l:
                if item not in r:
                    res.append(item)
            return res

        if isinstance(_rcontainer, list):
            return difference(_lcontainer, _rcontainer)
        else:
            lkeys = list(_lcontainer.keys())
            rkeys = list(_rcontainer.keys())
            diff = difference(lkeys, rkeys)
            result = {}
            for k in diff:
                result[k] = _lcontainer[k]
            return result

    @WordDecorator("( lcontainer:any rcontainer:any -- result:any )", "Set intersection between two containers")
    async def INTERSECTION(self, lcontainer: Any, rcontainer: Any) -> Any:
        _lcontainer = lcontainer if lcontainer is not None else []
        _rcontainer = rcontainer if rcontainer is not None else []

        def intersection(l: list, r: list) -> list:
            res = []
            for item in l:
                if item in r:
                    res.append(item)
            return res

        if isinstance(_rcontainer, list):
            return intersection(_lcontainer, _rcontainer)
        else:
            lkeys = list(_lcontainer.keys())
            rkeys = list(_rcontainer.keys())
            inter = intersection(lkeys, rkeys)
            result = {}
            for k in inter:
                result[k] = _lcontainer[k]
            return result

    @WordDecorator("( lcontainer:any rcontainer:any -- result:any )", "Set union between two containers")
    async def UNION(self, lcontainer: Any, rcontainer: Any) -> Any:
        if lcontainer is None:
            lcontainer = []
        if rcontainer is None:
            rcontainer = []

        def union(l: list, r: list) -> list:
            keyset: dict = {}
            for item in l:
                keyset[item] = True
            for item in r:
                keyset[item] = True
            return list(keyset.keys())

        if isinstance(rcontainer, list):
            result = union(lcontainer, rcontainer)
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

    # ==================
    # Sort
    # ==================

    @WordDecorator(
        "( container:any[] [options:WordOptions] -- array:any[] )",
        "Sort container. Options: comparator (string or function)",
    )
    async def SORT(self, container: list, options: dict[str, Any]) -> list:
        if container is None:
            return container
        if not isinstance(container, list):
            return container

        interp = self._module.interp
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

            def cmp_items(l: tuple, r: tuple) -> int:
                l_val = l[1]
                r_val = r[1]

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
            def cmp_items(l: Any, r: Any) -> int:
                l_val = key_func(l)
                r_val = key_func(r)
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

    @WordDecorator("( array:any[] -- array:any[] )", "Shuffle array randomly")
    async def SHUFFLE(self, array: list) -> list:
        if array is None:
            return array

        result = array.copy()
        random.shuffle(result)
        return result

    # ==================
    # Group
    # ==================

    @WordDecorator("( items:any[] forthic:string -- indexed:any )", "Create index mapping from array indices to values")
    async def INDEX(self, items: list, forthic: str) -> dict:
        interp = self._module.interp
        string_location = interp.get_string_location()

        if items is None:
            return {}

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

    @WordDecorator("( container:any[] field:string -- indexed:any )", "Index records by field value")
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
            if v:
                result[v[field]] = v

        return result

    @WordDecorator("( container:any[] field:string -- grouped:any )", "Group records by field value")
    async def GROUP_BY_FIELD(self, container: list, field: str) -> dict:
        if container is None:
            container = []

        if isinstance(container, list):
            values = container
        else:
            values = [container[k] for k in container.keys()]

        result: dict = {}
        for v in values:
            field_val = v[field]
            if isinstance(field_val, list):
                for fv in field_val:
                    if fv not in result:
                        result[fv] = []
                    result[fv].append(v)
            else:
                if field_val not in result:
                    result[field_val] = []
                result[field_val].append(v)

        return result

    @DirectWord(
        "( items:any forthic:string [options:WordOptions] -- grouped:any )",
        "Group items by function result. Options: with_key (bool)"
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
            group_key = interp.stack_pop()
            # Convert numeric keys to strings to match JavaScript/TypeScript behavior
            if isinstance(group_key, (int, float)):
                group_key = str(int(group_key))
            if group_key not in result:
                result[group_key] = []
            result[group_key].append(item)

        if isinstance(items, list):
            for i, item in enumerate(items):
                await process_item(item, i)
        else:
            for key in items.keys():
                await process_item(items[key], key)

        interp.stack_push(result)

    @WordDecorator("( container:any[] n:number -- groups:any[] )", "Split array into groups of size n", "GROUPS_OF")
    async def GROUPS_OF(self, container: list, n: int) -> list:
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

    @DirectWord(
        "( items:any forthic:string [options:WordOptions] -- )",
        "Execute forthic for each item. Options: with_key (bool), push_error (bool)",
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

        flags = {
            "with_key": options_dict.get("with_key"),
            "push_error": options_dict.get("push_error"),
        }

        errors: list = []

        async def execute_with_error(forthic_str: str, location: Any) -> Any:
            try:
                await interp.run(forthic_str, location)
                return None
            except Exception as error:
                return error

        if isinstance(items, list):
            for i, item in enumerate(items):
                if flags["with_key"]:
                    interp.stack_push(i)
                interp.stack_push(item)

                if flags["push_error"]:
                    error = await execute_with_error(forthic, string_location)
                    errors.append(error)
                else:
                    await interp.run(forthic, string_location)
        else:
            for k in items.keys():
                item = items[k]
                if flags["with_key"]:
                    interp.stack_push(k)
                interp.stack_push(item)

                if flags["push_error"]:
                    error = await execute_with_error(forthic, string_location)
                    errors.append(error)
                else:
                    await interp.run(forthic, string_location)

        if flags["push_error"]:
            interp.stack_push(errors)

    @DirectWord("( container:list initial:any forthic:str -- result:any )", "Reduce array or record with accumulator")
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
        "( container:any [options:WordOptions] -- flat:any )", "Flatten nested arrays or records. Options: depth (number)"
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
            result = flatten_array(container, depth, [])
        else:
            result = flatten_record(container, depth, {}, [])

        return result

    @DirectWord("( item:any forthic:string num_times:number -- )", "Repeat execution of forthic num_times", "<REPEAT")
    async def l_REPEAT(self, interp: Interpreter) -> None:
        num_times = interp.stack_pop()
        forthic = interp.stack_pop()
        string_location = interp.get_string_location()

        for _ in range(num_times):
            # Store item so we can push it back later
            item = interp.stack_pop()
            interp.stack_push(item)

            await interp.run(forthic, string_location)
            res = interp.stack_pop()

            # Push original item and result
            interp.stack_push(item)
            interp.stack_push(res)
