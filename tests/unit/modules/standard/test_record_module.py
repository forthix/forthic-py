"""Tests for Record Module - ported from TypeScript."""

import pytest

from forthic import StandardInterpreter


@pytest.fixture
def interp():
    """Create a fresh StandardInterpreter for each test."""
    return StandardInterpreter()


# ========================================
# Create Operations
# ========================================


class TestCreateOperations:
    """Test record creation operations."""

    @pytest.mark.asyncio
    async def test_rec(self, interp):
        """Test REC creates record from array of pairs."""
        await interp.run("[['alpha' 2] ['beta' 3] ['gamma' 4]] REC")
        rec = interp.stack_pop()
        assert rec["alpha"] == 2
        assert rec["beta"] == 3
        assert rec["gamma"] == 4

    @pytest.mark.asyncio
    async def test_rec_at_simple(self, interp):
        """Test REC@ retrieves value from record."""
        await interp.run("""
            [['alpha' 2] ['beta' 3] ['gamma' 4]] REC
            'beta' REC@
        """)
        assert interp.stack_pop() == 3

    @pytest.mark.asyncio
    async def test_rec_at_with_array_index(self, interp):
        """Test REC@ with array index."""
        await interp.run("[10 20 30 40 50] 3 REC@")
        assert interp.stack_pop() == 40

    @pytest.mark.asyncio
    async def test_rec_at_nested(self, interp):
        """Test REC@ with nested paths."""
        await interp.run("""
            [['alpha' [['alpha1' 20]] REC]
             ['beta' [['beta1'  30]] REC]
            ] REC
            ['beta' 'beta1'] REC@
        """)
        assert interp.stack_pop() == 30

        await interp.run("""
            [['alpha' [['alpha1' 20]] REC]
             ['beta' [['beta1'  [10 20 30]]] REC]
            ] REC
            ['beta' 'beta1' 1] REC@
        """)
        assert interp.stack_pop() == 20

    @pytest.mark.asyncio
    async def test_l_rec_bang_simple(self, interp):
        """Test <REC! stores value in record."""
        await interp.run("""
            [['alpha' 2] ['beta' 3] ['gamma' 4]] REC
            700 'beta' <REC! 'beta' REC@
        """)
        assert interp.stack_pop() == 700

    @pytest.mark.asyncio
    async def test_l_rec_bang_nested_creation(self, interp):
        """Test <REC! creates nested structure."""
        await interp.run("""
            NULL 42 ['a' 'b' 'c'] <REC!
            ['a' 'b' 'c'] REC@
        """)
        assert interp.stack_pop() == 42


# ========================================
# Transform Operations
# ========================================


class TestTransformOperations:
    """Test record transformation operations."""

    @pytest.mark.asyncio
    async def test_relabel_record(self, interp):
        """Test RELABEL renames keys."""
        await interp.run("""
            [['a' 1] ['b' 2] ['c' 3]] REC
            ['a' 'b' 'c'] ['alpha' 'beta' 'gamma'] RELABEL
        """)
        rec = interp.stack_pop()
        assert rec["alpha"] == 1
        assert rec["beta"] == 2
        assert rec["gamma"] == 3

    @pytest.mark.asyncio
    async def test_invert_keys(self, interp):
        """Test INVERT-KEYS transposes nested records."""
        await interp.run("""
            [
                ['x' [['a' 1] ['b' 2]] REC]
                ['y' [['a' 10] ['b' 20]] REC]
            ] REC
            INVERT-KEYS
        """)
        result = interp.stack_pop()
        assert result["a"]["x"] == 1
        assert result["a"]["y"] == 10
        assert result["b"]["x"] == 2
        assert result["b"]["y"] == 20

    @pytest.mark.asyncio
    async def test_rec_defaults_is_gone(self, interp):
        """Tombstone: REC-DEFAULTS dropped for MERGE. Migration note:
        REC-DEFAULTS also overrode NULL/"" values; MERGE is key-presence
        only — write defaults first and MERGE the real record over them."""
        with pytest.raises(Exception, match="REC-DEFAULTS"):
            await interp.run("[ ] REC [ ] REC REC-DEFAULTS")

    @pytest.mark.asyncio
    async def test_merge_replaces_rec_defaults(self, interp):
        """The REC-DEFAULTS use case via MERGE (defaults first)."""
        await interp.run("""
            [['b' 100] ['c' 200] ['d' 300]] REC
            [['a' 1] ['b' 2]] REC
            MERGE
        """)
        rec = interp.stack_pop()
        assert rec == {"b": 2, "c": 200, "d": 300, "a": 1}

    @pytest.mark.asyncio
    async def test_classic_l_del_is_gone(self, interp):
        """Tombstone: <DEL dropped for DELETE. Note <DEL MUTATED its input
        in place; DELETE is copy-on-write."""
        with pytest.raises(Exception, match="DEL"):
            await interp.run("[['a' 1]] REC 'a' <DEL")

    @pytest.mark.asyncio
    async def test_delete_from_record(self, interp):
        """DELETE removes key from record, preserving order (copy-on-write)."""
        await interp.run("""
            [['a' 1] ['b' 2] ['c' 3]] REC
            'b' DELETE
        """)
        rec = interp.stack_pop()
        assert list(rec.keys()) == ["a", "c"]

    @pytest.mark.asyncio
    async def test_delete_from_array(self, interp):
        """DELETE removes index from array (copy-on-write)."""
        await interp.run("""
            [10 20 30 40]
            1 DELETE
        """)
        arr = interp.stack_pop()
        assert arr == [10, 30, 40]


# ========================================
# Access Operations
# ========================================


class TestAccessOperations:
    """Test record access operations."""

    @pytest.mark.asyncio
    async def test_keys_from_array(self, interp):
        """Test KEYS from array returns indices."""
        await interp.run("['a' 'b' 'c'] KEYS")
        assert interp.stack_pop() == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_keys_from_record(self, interp):
        """Test KEYS from record returns keys."""
        await interp.run("[['a' 1] ['b' 2]] REC KEYS")
        keys = interp.stack_pop()
        assert sorted(keys) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_values_from_array(self, interp):
        """Test VALUES from array."""
        await interp.run("['a' 'b' 'c'] VALUES")
        assert interp.stack_pop() == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_values_from_record(self, interp):
        """Test VALUES from record."""
        await interp.run("[['a' 1] ['b' 2]] REC VALUES")
        values = interp.stack_pop()
        assert sorted(values) == [1, 2]


# ========================================
# Advanced Operations
# ========================================


class TestAdvancedOperations:
    """Test advanced record operations."""

    @pytest.mark.asyncio
    async def test_pipe_rec_at_is_gone(self, interp):
        """Tombstone: |REC@ removed (injection-shaped: it json.dumps'd the
        field into a Forthic string and ran it — ts removed it in #27).
        The composition is 'FIELD REC@' MAP."""
        with pytest.raises(Exception, match="REC@"):
            await interp.run("[ ] 'key' |REC@")

    @pytest.mark.asyncio
    async def test_pipe_rec_at_replacement_composition(self, interp):
        """The |REC@ use case via MAP + REC@."""
        await interp.run("""
            [
                [['key' 101] ['value' 'alpha']] REC
                [['key' 102] ['value' 'beta']] REC
                [['key' 103] ['value' 'gamma']] REC
            ]
            "'key' REC@" MAP
        """)
        keys = interp.stack_pop()
        assert keys == [101, 102, 103]
