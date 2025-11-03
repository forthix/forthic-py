"""Record module - Record (object/dictionary) manipulation operations.

Provides operations for working with key-value data structures.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

from ...decorators import DecoratedModule, register_module_doc
from ...decorators import ForthicWord as WordDecorator


class RecordModule(DecoratedModule):
    """Record (object/dictionary) manipulation operations for working with key-value data structures."""

    def __init__(self):
        super().__init__("record")
        register_module_doc(
            RecordModule,
            """
Record (object/dictionary) manipulation operations for working with key-value data structures.

## Categories
- Core: REC, REC@, |REC@, <REC!
- Transform: RELABEL, INVERT_KEYS, REC_DEFAULTS, <DEL
- Access: KEYS, VALUES
            """,
        )

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
        _key_vals = key_vals if key_vals else []

        result: dict = {}
        for pair in _key_vals:
            key = None
            val = None
            if pair:
                if len(pair) >= 1:
                    key = pair[0]
                if len(pair) >= 2:
                    val = pair[1]
            result[key] = val

        return result

    @WordDecorator("( rec:any field:any -- value:any )", "Get value from record by field or array of fields", "REC@")
    async def REC_at(self, rec: Any, field: Any) -> Any:
        if not rec:
            return None

        fields = [field]
        if isinstance(field, list):
            fields = field

        result = RecordModule.drill_for_value(rec, fields)
        return result

    @WordDecorator("( records:any field:any -- values:any )", "Map REC@ over array of records", "|REC@")
    async def pipe_REC_at(self, records: Any, field: Any) -> Any:
        # Push records back and field, then use MAP with REC@
        self._module.interp.stack_push(records)
        await self._module.interp.run(f"'{json.dumps(field)} REC@' MAP")
        # Result already on stack from MAP, return None to avoid double-push
        return None

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

    @WordDecorator("( record:any -- inverted:any )", "Invert two-level nested record structure", "INVERT_KEYS")
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

    @WordDecorator(
        "( record:any key_vals:any[] -- record:any )", "Set default values for missing/empty fields", "REC_DEFAULTS"
    )
    async def REC_DEFAULTS(self, record: dict, key_vals: list) -> dict:
        for key_val in key_vals:
            key = key_val[0]
            value = record.get(key)
            if value is None or value == "":
                record[key] = key_val[1]

        return record

    @WordDecorator("( container:any key:any -- container:any )", "Delete key from record or index from array", "<DEL")
    async def l_DEL(self, container: Any, key: Any) -> Any:
        if not container:
            return container

        if isinstance(container, list):
            del container[key]
        else:
            if key in container:
                del container[key]

        return container

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
