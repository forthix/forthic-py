"""Tests for Pandas Module."""

import pytest

try:
    import pandas as pd
except ImportError:
    pytest.skip("pandas not installed", allow_module_level=True)

from forthic import StandardInterpreter


@pytest.fixture
def interp():
    """Create a fresh StandardInterpreter for each test."""
    from forthic.modules import PandasModule

    interp = StandardInterpreter()
    # Register and import pandas module with prefix "pd"
    # import_module now handles DecoratedModule automatically
    pandas_module = PandasModule()
    interp.import_module(pandas_module, "pd")
    return interp


@pytest.fixture
def sample_records():
    """Sample records for testing DataFrame conversion."""
    return [
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "LA"},
        {"name": "Charlie", "age": 35, "city": "NYC"},
        {"name": "David", "age": 28, "city": "SF"},
    ]


@pytest.fixture
def sample_df(sample_records):
    """Sample DataFrame for testing."""
    return pd.DataFrame(sample_records)


# ========================================
# Conversion Operations
# ========================================


class TestConversionOperations:
    """Test DataFrame/Series conversion operations."""

    @pytest.mark.asyncio
    async def test_to_df_from_records(self, interp, sample_records):
        """Test >DF converts list of records to DataFrame."""
        # Push sample records and convert to DataFrame
        interp.stack_push(sample_records)
        await interp.run("pd.>DF")

        df = interp.stack_pop()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        assert list(df.columns) == ["name", "age", "city"]
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[1]["age"] == 25

    @pytest.mark.asyncio
    async def test_to_df_from_empty_list(self, interp):
        """Test >DF with empty list returns empty DataFrame."""
        await interp.run("[] pd.>DF")
        df = interp.stack_pop()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @pytest.mark.asyncio
    async def test_df_to_records(self, interp, sample_df):
        """Test DF> converts DataFrame to list of records."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF>")

        records = interp.stack_pop()
        assert isinstance(records, list)
        assert len(records) == 4
        assert records[0]["name"] == "Alice"
        assert records[1]["age"] == 25
        assert records[2]["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_df_to_records_empty(self, interp):
        """Test DF> with empty DataFrame returns empty list."""
        interp.stack_push(pd.DataFrame())
        await interp.run("pd.DF>")

        records = interp.stack_pop()
        assert records == []

    @pytest.mark.asyncio
    async def test_to_series_simple(self, interp):
        """Test >SERIES converts list to Series."""
        await interp.run("[1 2 3 4 5] pd.>SERIES")

        series = interp.stack_pop()
        assert isinstance(series, pd.Series)
        assert len(series) == 5
        assert series.tolist() == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_to_series_with_index(self, interp):
        """Test >SERIES with custom index."""
        await interp.run("""
            [10 20 30]
            [.index ['a' 'b' 'c']] ~> pd.>SERIES
        """)

        series = interp.stack_pop()
        assert isinstance(series, pd.Series)
        assert series["a"] == 10
        assert series["b"] == 20
        assert series["c"] == 30

    @pytest.mark.asyncio
    async def test_to_series_with_name(self, interp):
        """Test >SERIES with custom name."""
        await interp.run("""
            [100 200 300]
            [.name 'values'] ~> pd.>SERIES
        """)

        series = interp.stack_pop()
        assert isinstance(series, pd.Series)
        assert series.name == "values"
        assert series.tolist() == [100, 200, 300]

    @pytest.mark.asyncio
    async def test_series_to_list(self, interp):
        """Test SERIES> converts Series to list."""
        series = pd.Series([10, 20, 30, 40])
        interp.stack_push(series)
        await interp.run("pd.SERIES>")

        values = interp.stack_pop()
        assert values == [10, 20, 30, 40]

    @pytest.mark.asyncio
    async def test_series_to_list_empty(self, interp):
        """Test SERIES> with empty Series returns empty list."""
        interp.stack_push(pd.Series([]))
        await interp.run("pd.SERIES>")

        values = interp.stack_pop()
        assert values == []


# ========================================
# Inspection Operations
# ========================================


class TestInspectionOperations:
    """Test DataFrame inspection operations."""

    @pytest.mark.asyncio
    async def test_df_info(self, interp, sample_df, capsys):
        """Test DF.INFO prints info and returns DataFrame."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.INFO")

        df = interp.stack_pop()
        assert isinstance(df, pd.DataFrame)
        assert df.equals(sample_df)

        # Check that info was printed
        captured = capsys.readouterr()
        assert "name" in captured.out or "RangeIndex" in captured.out

    @pytest.mark.asyncio
    async def test_df_head_default(self, interp, sample_df):
        """Test DF.HEAD returns first 5 rows by default."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.HEAD")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4  # Sample has only 4 rows

    @pytest.mark.asyncio
    async def test_df_head_with_n(self, interp, sample_df):
        """Test DF.HEAD with custom n."""
        interp.stack_push(sample_df)
        await interp.run("[.n 2] ~> pd.DF.HEAD")

        result = interp.stack_pop()
        assert len(result) == 2
        assert result.iloc[0]["name"] == "Alice"
        assert result.iloc[1]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_df_tail_default(self, interp, sample_df):
        """Test DF.TAIL returns last 5 rows by default."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.TAIL")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4  # Sample has only 4 rows

    @pytest.mark.asyncio
    async def test_df_tail_with_n(self, interp, sample_df):
        """Test DF.TAIL with custom n."""
        interp.stack_push(sample_df)
        await interp.run("[.n 2] ~> pd.DF.TAIL")

        result = interp.stack_pop()
        assert len(result) == 2
        assert result.iloc[0]["name"] == "Charlie"
        assert result.iloc[1]["name"] == "David"

    @pytest.mark.asyncio
    async def test_df_shape(self, interp, sample_df):
        """Test DF.SHAPE returns [rows, cols]."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.SHAPE")

        shape = interp.stack_pop()
        assert shape == [4, 3]

    @pytest.mark.asyncio
    async def test_df_columns(self, interp, sample_df):
        """Test DF.COLUMNS returns list of column names."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.COLUMNS")

        columns = interp.stack_pop()
        assert columns == ["name", "age", "city"]

    @pytest.mark.asyncio
    async def test_df_dtypes(self, interp, sample_df):
        """Test DF.DTYPES returns column types as dict."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.DTYPES")

        dtypes = interp.stack_pop()
        assert isinstance(dtypes, dict)
        assert "name" in dtypes
        assert "age" in dtypes
        assert "city" in dtypes
        assert "int" in dtypes["age"] or "Int" in dtypes["age"]

    @pytest.mark.asyncio
    async def test_df_describe(self, interp, sample_df):
        """Test DF.DESCRIBE returns summary statistics."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.DESCRIBE")

        stats = interp.stack_pop()
        assert isinstance(stats, pd.DataFrame)
        assert "age" in stats.columns  # Numeric column should be described
        assert "count" in stats.index or stats.index[0] == "count"

    @pytest.mark.asyncio
    async def test_df_nunique(self, interp, sample_df):
        """Test DF.NUNIQUE counts unique values per column."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.NUNIQUE")

        counts = interp.stack_pop()
        assert isinstance(counts, dict)
        assert counts["name"] == 4  # All unique names
        assert counts["city"] == 3  # NYC, LA, SF


# ========================================
# Integration Tests
# ========================================


class TestIntegration:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_round_trip_conversion(self, interp, sample_records):
        """Test converting records -> DataFrame -> records."""
        interp.stack_push(sample_records)
        await interp.run("pd.>DF pd.DF>")

        result = interp.stack_pop()
        assert result == sample_records

    @pytest.mark.asyncio
    async def test_chaining_operations(self, interp, sample_records):
        """Test chaining multiple operations."""
        interp.stack_push(sample_records)
        await interp.run("""
            pd.>DF
            [.n 2] ~> pd.DF.HEAD
            pd.DF.COLUMNS
        """)

        columns = interp.stack_pop()
        assert columns == ["name", "age", "city"]

    @pytest.mark.asyncio
    async def test_series_operations(self, interp):
        """Test Series creation and conversion."""
        await interp.run("""
            [5 10 15 20]
            [.index ['a' 'b' 'c' 'd'] .name 'my_series'] ~> pd.>SERIES
            pd.SERIES>
        """)

        values = interp.stack_pop()
        assert values == [5, 10, 15, 20]


# ========================================
# Column Operations
# ========================================


class TestColumnOperations:
    """Test DataFrame column access and manipulation."""

    @pytest.mark.asyncio
    async def test_df_at_single_column(self, interp, sample_df):
        """Test DF@ gets single column as Series."""
        interp.stack_push(sample_df)
        await interp.run("'name' pd.DF@")

        series = interp.stack_pop()
        assert isinstance(series, pd.Series)
        assert len(series) == 4
        assert series.tolist() == ["Alice", "Bob", "Charlie", "David"]

    @pytest.mark.asyncio
    async def test_df_at_nonexistent_column(self, interp, sample_df):
        """Test DF@ raises KeyError for nonexistent column."""
        interp.stack_push(sample_df)

        with pytest.raises(KeyError, match="not found"):
            await interp.run("'invalid' pd.DF@")

    @pytest.mark.asyncio
    async def test_df_at_at_multiple_columns(self, interp, sample_df):
        """Test DF@@ gets multiple columns as DataFrame."""
        interp.stack_push(sample_df)
        await interp.run("['name' 'age'] pd.DF@@")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "age"]
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_df_at_at_empty_list(self, interp, sample_df):
        """Test DF@@ with empty list returns empty DataFrame."""
        interp.stack_push(sample_df)
        await interp.run("[] pd.DF@@")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_df_at_at_missing_columns(self, interp, sample_df):
        """Test DF@@ raises KeyError for missing columns."""
        interp.stack_push(sample_df)

        with pytest.raises(KeyError, match="not found"):
            await interp.run("['name' 'invalid'] pd.DF@@")

    @pytest.mark.asyncio
    async def test_l_df_bang_add_column(self, interp, sample_df):
        """Test <DF! adds new column to DataFrame."""
        interp.stack_push(sample_df)
        series = pd.Series([100, 200, 300, 400])
        interp.stack_push(series)
        await interp.run("'salary' pd.<DF!")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert "salary" in result.columns
        assert result["salary"].tolist() == [100, 200, 300, 400]

    @pytest.mark.asyncio
    async def test_l_df_bang_replace_column(self, interp, sample_df):
        """Test <DF! replaces existing column."""
        interp.stack_push(sample_df)
        series = pd.Series([31, 26, 36, 29])
        interp.stack_push(series)
        await interp.run("'age' pd.<DF!")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result["age"].tolist() == [31, 26, 36, 29]

    @pytest.mark.asyncio
    async def test_df_drop_cols(self, interp, sample_df):
        """Test DF.DROP-COLS removes columns."""
        interp.stack_push(sample_df)
        await interp.run("['age'] pd.DF.DROP-COLS")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert "age" not in result.columns
        assert list(result.columns) == ["name", "city"]

    @pytest.mark.asyncio
    async def test_df_drop_cols_multiple(self, interp, sample_df):
        """Test DF.DROP-COLS removes multiple columns."""
        interp.stack_push(sample_df)
        await interp.run("['age' 'city'] pd.DF.DROP-COLS")

        result = interp.stack_pop()
        assert list(result.columns) == ["name"]

    @pytest.mark.asyncio
    async def test_df_drop_cols_empty_list(self, interp, sample_df):
        """Test DF.DROP-COLS with empty list returns unchanged DataFrame."""
        interp.stack_push(sample_df)
        await interp.run("[] pd.DF.DROP-COLS")

        result = interp.stack_pop()
        assert list(result.columns) == ["name", "age", "city"]

    @pytest.mark.asyncio
    async def test_df_rename_cols(self, interp, sample_df):
        """Test DF.RENAME-COLS renames columns."""
        interp.stack_push(sample_df)
        await interp.run("""
            [['name' 'full_name'] ['age' 'years']] REC
            pd.DF.RENAME-COLS
        """)

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["full_name", "years", "city"]

    @pytest.mark.asyncio
    async def test_df_rename_cols_empty_mapping(self, interp, sample_df):
        """Test DF.RENAME-COLS with empty mapping returns unchanged DataFrame."""
        interp.stack_push(sample_df)
        await interp.run("[[] []] REC pd.DF.RENAME-COLS")

        result = interp.stack_pop()
        assert list(result.columns) == ["name", "age", "city"]

    @pytest.mark.asyncio
    async def test_df_select_dtypes_single(self, interp):
        """Test DF.SELECT-DTYPES with single dtype."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [1.5, 2.5, 3.5]})
        interp.stack_push(df)
        await interp.run("'object' pd.DF.SELECT-DTYPES")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["b"]

    @pytest.mark.asyncio
    async def test_df_select_dtypes_multiple(self, interp):
        """Test DF.SELECT-DTYPES with multiple dtypes."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [1.5, 2.5, 3.5]})
        interp.stack_push(df)
        await interp.run("'number' pd.DF.SELECT-DTYPES")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        # Should include both int and float columns
        assert "a" in result.columns
        assert "c" in result.columns
        assert "b" not in result.columns

    @pytest.mark.asyncio
    async def test_df_apply_col_simple(self, interp, sample_df):
        """Test DF.APPLY-COL applies Forthic to column values."""
        interp.stack_push(sample_df)
        await interp.run("'age' '2 *' pd.DF.APPLY-COL")

        series = interp.stack_pop()
        assert isinstance(series, pd.Series)
        assert series.tolist() == [60, 50, 70, 56]

    @pytest.mark.asyncio
    async def test_df_apply_col_complex(self, interp, sample_df):
        """Test DF.APPLY-COL with complex Forthic expression."""
        interp.stack_push(sample_df)
        await interp.run("'age' '10 + 2 /' pd.DF.APPLY-COL")

        series = interp.stack_pop()
        assert isinstance(series, pd.Series)
        # (age + 10) / 2
        assert series.tolist() == [20, 17.5, 22.5, 19]

    @pytest.mark.asyncio
    async def test_df_apply_col_missing_column(self, interp, sample_df):
        """Test DF.APPLY-COL raises error for missing column."""
        interp.stack_push(sample_df)

        with pytest.raises(KeyError, match="not found"):
            await interp.run("'invalid' '2 *' pd.DF.APPLY-COL")

    @pytest.mark.asyncio
    async def test_df_astype(self, interp):
        """Test DF.ASTYPE converts column dtype."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4.5, 5.5, 6.5]})
        interp.stack_push(df)
        await interp.run("'a' 'float' pd.DF.ASTYPE")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result["a"].dtype == float

    @pytest.mark.asyncio
    async def test_df_astype_to_string(self, interp, sample_df):
        """Test DF.ASTYPE converts column to string."""
        interp.stack_push(sample_df)
        await interp.run("'age' 'str' pd.DF.ASTYPE")

        result = interp.stack_pop()
        assert result["age"].dtype == object  # strings are stored as object type
        assert result["age"].tolist() == ["30", "25", "35", "28"]

    @pytest.mark.asyncio
    async def test_df_astype_missing_column(self, interp, sample_df):
        """Test DF.ASTYPE raises error for missing column."""
        interp.stack_push(sample_df)

        with pytest.raises(KeyError, match="not found"):
            await interp.run("'invalid' 'str' pd.DF.ASTYPE")


# ========================================
# Row Operations
# ========================================


class TestRowOperations:
    """Test DataFrame row access and filtering."""

    @pytest.mark.asyncio
    async def test_df_iloc_single_row(self, interp, sample_df):
        """Test DF.ILOC gets row by position as record."""
        interp.stack_push(sample_df)
        await interp.run("0 pd.DF.ILOC")

        record = interp.stack_pop()
        assert isinstance(record, dict)
        assert record["name"] == "Alice"
        assert record["age"] == 30
        assert record["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_df_iloc_last_row(self, interp, sample_df):
        """Test DF.ILOC gets last row."""
        interp.stack_push(sample_df)
        await interp.run("3 pd.DF.ILOC")

        record = interp.stack_pop()
        assert record["name"] == "David"
        assert record["age"] == 28

    @pytest.mark.asyncio
    async def test_df_iloc_out_of_range(self, interp, sample_df):
        """Test DF.ILOC raises IndexError for out of range index."""
        interp.stack_push(sample_df)

        with pytest.raises(IndexError, match="out of range"):
            await interp.run("10 pd.DF.ILOC")

    @pytest.mark.asyncio
    async def test_df_loc_by_label(self, interp):
        """Test DF.LOC gets row by label as record."""
        df = pd.DataFrame(
            {"name": ["Alice", "Bob"], "age": [30, 25]}, index=["person1", "person2"]
        )
        interp.stack_push(df)
        await interp.run("'person1' pd.DF.LOC")

        record = interp.stack_pop()
        assert isinstance(record, dict)
        assert record["name"] == "Alice"
        assert record["age"] == 30

    @pytest.mark.asyncio
    async def test_df_loc_missing_label(self, interp):
        """Test DF.LOC raises KeyError for missing label."""
        df = pd.DataFrame(
            {"name": ["Alice", "Bob"], "age": [30, 25]}, index=["person1", "person2"]
        )
        interp.stack_push(df)

        with pytest.raises(KeyError, match="not found"):
            await interp.run("'invalid' pd.DF.LOC")

    @pytest.mark.asyncio
    async def test_df_filter_simple(self, interp, sample_df):
        """Test DF.FILTER filters rows with Forthic predicate."""
        interp.stack_push(sample_df)
        await interp.run("'\"age\" REC@ 30 >=' pd.DF.FILTER")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]["name"] == "Alice"
        assert result.iloc[1]["name"] == "Charlie"

    @pytest.mark.asyncio
    async def test_df_filter_string_match(self, interp, sample_df):
        """Test DF.FILTER with string matching."""
        interp.stack_push(sample_df)
        await interp.run("'\"city\" REC@ \"NYC\" ==' pd.DF.FILTER")

        result = interp.stack_pop()
        assert len(result) == 2
        assert result.iloc[0]["name"] == "Alice"
        assert result.iloc[1]["name"] == "Charlie"

    @pytest.mark.asyncio
    async def test_df_filter_no_matches(self, interp, sample_df):
        """Test DF.FILTER returns empty DataFrame when no rows match."""
        interp.stack_push(sample_df)
        await interp.run("'\"age\" REC@ 100 >' pd.DF.FILTER")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_df_drop_rows_single(self, interp):
        """Test DF.DROP-ROWS removes single row by index."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("[1] pd.DF.DROP-ROWS")

        result = interp.stack_pop()
        assert len(result) == 2
        assert result.iloc[0]["a"] == 1
        assert result.iloc[1]["a"] == 3

    @pytest.mark.asyncio
    async def test_df_drop_rows_multiple(self, interp):
        """Test DF.DROP-ROWS removes multiple rows."""
        df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]})
        interp.stack_push(df)
        await interp.run("[0 2] pd.DF.DROP-ROWS")

        result = interp.stack_pop()
        assert len(result) == 2
        assert result.iloc[0]["a"] == 2
        assert result.iloc[1]["a"] == 4

    @pytest.mark.asyncio
    async def test_df_drop_rows_empty_list(self, interp, sample_df):
        """Test DF.DROP-ROWS with empty list returns unchanged DataFrame."""
        interp.stack_push(sample_df)
        await interp.run("[] pd.DF.DROP-ROWS")

        result = interp.stack_pop()
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_df_append_row(self, interp, sample_df):
        """Test DF.APPEND-ROW adds a row to DataFrame."""
        interp.stack_push(sample_df)
        await interp.run("""
            [['name' 'Eve'] ['age' 32] ['city' 'Boston']] REC
            pd.DF.APPEND-ROW
        """)

        result = interp.stack_pop()
        assert len(result) == 5
        assert result.iloc[4]["name"] == "Eve"
        assert result.iloc[4]["age"] == 32
        assert result.iloc[4]["city"] == "Boston"

    @pytest.mark.asyncio
    async def test_df_append_row_to_empty(self, interp):
        """Test DF.APPEND-ROW to empty DataFrame."""
        interp.stack_push(pd.DataFrame())
        await interp.run("""
            [['name' 'Alice'] ['age' 30]] REC
            pd.DF.APPEND-ROW
        """)

        result = interp.stack_pop()
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_df_sample_default(self, interp, sample_df):
        """Test DF.SAMPLE returns 1 row by default."""
        interp.stack_push(sample_df)
        await interp.run("pd.DF.SAMPLE")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_df_sample_with_n(self, interp, sample_df):
        """Test DF.SAMPLE with custom n."""
        interp.stack_push(sample_df)
        await interp.run("[.n 2 .random_state 42] ~> pd.DF.SAMPLE")

        result = interp.stack_pop()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_df_sample_with_frac(self, interp, sample_df):
        """Test DF.SAMPLE with fraction."""
        interp.stack_push(sample_df)
        await interp.run("[.frac 0.5 .random_state 42] ~> pd.DF.SAMPLE")

        result = interp.stack_pop()
        assert len(result) == 2  # 50% of 4 rows

    @pytest.mark.asyncio
    async def test_df_nlargest(self, interp, sample_df):
        """Test DF.NLARGEST gets top N rows by column."""
        interp.stack_push(sample_df)
        await interp.run("'age' 2 pd.DF.NLARGEST")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]["name"] == "Charlie"  # age 35
        assert result.iloc[1]["name"] == "Alice"  # age 30

    @pytest.mark.asyncio
    async def test_df_nlargest_missing_column(self, interp, sample_df):
        """Test DF.NLARGEST raises error for missing column."""
        interp.stack_push(sample_df)

        with pytest.raises(KeyError, match="not found"):
            await interp.run("'invalid' 2 pd.DF.NLARGEST")


# ========================================
# Aggregation Operations
# ========================================


class TestAggregationOperations:
    """Test DataFrame aggregation operations."""

    @pytest.mark.asyncio
    async def test_df_group_by_single_column(self, interp, sample_df):
        """Test DF.GROUP-BY with single column."""
        interp.stack_push(sample_df)
        await interp.run("'city' pd.DF.GROUP-BY")

        grouped = interp.stack_pop()
        # GroupBy object should be returned
        assert hasattr(grouped, 'groups')
        assert len(grouped.groups) == 3  # NYC, LA, SF

    @pytest.mark.asyncio
    async def test_df_group_by_multiple_columns(self, interp):
        """Test DF.GROUP-BY with multiple columns."""
        df = pd.DataFrame({
            'city': ['NYC', 'NYC', 'LA', 'LA'],
            'dept': ['HR', 'IT', 'HR', 'IT'],
            'salary': [70000, 80000, 65000, 75000]
        })
        interp.stack_push(df)
        await interp.run("['city' 'dept'] pd.DF.GROUP-BY")

        grouped = interp.stack_pop()
        assert hasattr(grouped, 'groups')
        assert len(grouped.groups) == 4

    @pytest.mark.asyncio
    async def test_df_agg_with_function_name(self, interp, sample_df):
        """Test DF.AGG with function name."""
        interp.stack_push(sample_df)
        await interp.run("'city' pd.DF.GROUP-BY 'count' pd.DF.AGG")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_df_agg_with_dict(self, interp, sample_df):
        """Test DF.AGG with dict of aggregations."""
        interp.stack_push(sample_df)
        await interp.run("""
            [['age' 'mean'] ['name' 'count']] REC
            pd.DF.AGG
        """)

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_df_sum_default(self, interp):
        """Test DF.SUM with default axis."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("pd.DF.SUM")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result['a'] == 6
        assert result['b'] == 15

    @pytest.mark.asyncio
    async def test_df_sum_by_row(self, interp):
        """Test DF.SUM with axis=1 (by row)."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("[.axis 1] ~> pd.DF.SUM")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result.tolist() == [5, 7, 9]

    @pytest.mark.asyncio
    async def test_df_mean(self, interp):
        """Test DF.MEAN."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("pd.DF.MEAN")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result['a'] == 2.0
        assert result['b'] == 5.0

    @pytest.mark.asyncio
    async def test_df_median(self, interp):
        """Test DF.MEDIAN."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("pd.DF.MEDIAN")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result['a'] == 2.0
        assert result['b'] == 5.0

    @pytest.mark.asyncio
    async def test_df_count(self, interp):
        """Test DF.COUNT."""
        df = pd.DataFrame({'a': [1, 2, None], 'b': [4, None, 6]})
        interp.stack_push(df)
        await interp.run("pd.DF.COUNT")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result['a'] == 2  # 2 non-NA values
        assert result['b'] == 2  # 2 non-NA values

    @pytest.mark.asyncio
    async def test_df_value_counts(self, interp, sample_df):
        """Test DF.VALUE-COUNTS."""
        interp.stack_push(sample_df)
        await interp.run("'city' pd.DF@ pd.DF.VALUE-COUNTS")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result['NYC'] == 2
        assert result['LA'] == 1
        assert result['SF'] == 1

    @pytest.mark.asyncio
    async def test_df_pivot(self, interp):
        """Test DF.PIVOT."""
        df = pd.DataFrame({
            'date': ['2020-01-01', '2020-01-02', '2020-01-01', '2020-01-02'],
            'city': ['NYC', 'NYC', 'LA', 'LA'],
            'temp': [32, 35, 65, 68]
        })
        interp.stack_push(df)
        await interp.run("'temp' 'date' [.columns 'city'] ~> pd.DF.PIVOT")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert 'NYC' in result.columns
        assert 'LA' in result.columns

    @pytest.mark.asyncio
    async def test_df_pivot_table(self, interp):
        """Test DF.PIVOT-TABLE."""
        df = pd.DataFrame({
            'city': ['NYC', 'NYC', 'LA', 'LA'],
            'dept': ['HR', 'IT', 'HR', 'IT'],
            'salary': [70000, 80000, 65000, 75000]
        })
        interp.stack_push(df)
        await interp.run("""
            [.values 'salary' .index 'city' .columns 'dept' .aggfunc 'mean'] ~>
            pd.DF.PIVOT-TABLE
        """)

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_df_crosstab(self, interp, sample_df):
        """Test DF.CROSSTAB."""
        interp.stack_push(sample_df)
        await interp.run("'city' pd.DF@")
        city_series = interp.stack_pop()

        interp.stack_push(sample_df)
        await interp.run("'name' pd.DF@")
        name_series = interp.stack_pop()

        interp.stack_push(city_series)
        interp.stack_push(name_series)
        await interp.run("pd.DF.CROSSTAB")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)


# ========================================
# Statistical Operations
# ========================================


class TestStatisticalOperations:
    """Test DataFrame statistical operations."""

    @pytest.mark.asyncio
    async def test_df_corr_default(self, interp):
        """Test DF.CORR with default Pearson method."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [2, 4, 6, 8, 10],
            'c': [1, 3, 2, 4, 3]
        })
        interp.stack_push(df)
        await interp.run("pd.DF.CORR")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result.loc['a', 'b'] == 1.0  # Perfect positive correlation
        assert 'a' in result.columns
        assert 'b' in result.columns

    @pytest.mark.asyncio
    async def test_df_corr_with_method(self, interp):
        """Test DF.CORR with custom method."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [2, 4, 6, 8, 10]
        })
        interp.stack_push(df)
        await interp.run("[.method 'spearman'] ~> pd.DF.CORR")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_df_cov(self, interp):
        """Test DF.COV."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [2, 4, 6, 8, 10]
        })
        interp.stack_push(df)
        await interp.run("pd.DF.COV")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert 'a' in result.columns
        assert 'b' in result.columns

    @pytest.mark.asyncio
    async def test_df_rolling(self, interp):
        """Test DF.ROLLING creates rolling window object."""
        df = pd.DataFrame({'a': [1, 2, 3, 4, 5]})
        interp.stack_push(df)
        await interp.run("3 pd.DF.ROLLING")

        rolling = interp.stack_pop()
        assert hasattr(rolling, 'mean')  # Rolling object has aggregation methods

    @pytest.mark.asyncio
    async def test_df_rolling_with_options(self, interp):
        """Test DF.ROLLING with min_periods option."""
        df = pd.DataFrame({'a': [1, 2, 3, 4, 5]})
        interp.stack_push(df)
        await interp.run("3 [.min_periods 1] ~> pd.DF.ROLLING")

        rolling = interp.stack_pop()
        assert hasattr(rolling, 'mean')

    @pytest.mark.asyncio
    async def test_df_cumsum(self, interp):
        """Test DF.CUMSUM."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("pd.DF.CUMSUM")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [1, 3, 6]
        assert result['b'].tolist() == [4, 9, 15]

    @pytest.mark.asyncio
    async def test_df_cumsum_by_row(self, interp):
        """Test DF.CUMSUM with axis=1."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("[.axis 1] ~> pd.DF.CUMSUM")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result.iloc[0].tolist() == [1, 5]  # 1, 1+4
        assert result.iloc[1].tolist() == [2, 7]  # 2, 2+5

    @pytest.mark.asyncio
    async def test_df_cumprod(self, interp):
        """Test DF.CUMPROD."""
        df = pd.DataFrame({'a': [2, 3, 4], 'b': [1, 2, 3]})
        interp.stack_push(df)
        await interp.run("pd.DF.CUMPROD")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [2, 6, 24]  # 2, 2*3, 2*3*4
        assert result['b'].tolist() == [1, 2, 6]   # 1, 1*2, 1*2*3

    @pytest.mark.asyncio
    async def test_df_diff(self, interp):
        """Test DF.DIFF."""
        df = pd.DataFrame({'a': [10, 20, 30, 40], 'b': [5, 15, 25, 35]})
        interp.stack_push(df)
        await interp.run("pd.DF.DIFF")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        # First row is NaN, then differences
        import math
        assert math.isnan(result['a'].iloc[0])
        assert result['a'].iloc[1] == 10  # 20 - 10
        assert result['a'].iloc[2] == 10  # 30 - 20

    @pytest.mark.asyncio
    async def test_df_diff_with_periods(self, interp):
        """Test DF.DIFF with custom periods."""
        df = pd.DataFrame({'a': [10, 20, 30, 40]})
        interp.stack_push(df)
        await interp.run("[.periods 2] ~> pd.DF.DIFF")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        # First two rows are NaN, then differences of 2 periods
        assert result['a'].iloc[2] == 20  # 30 - 10

    @pytest.mark.asyncio
    async def test_df_pct_change(self, interp):
        """Test DF.PCT-CHANGE."""
        df = pd.DataFrame({'a': [100, 150, 120]})
        interp.stack_push(df)
        await interp.run("pd.DF.PCT-CHANGE")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        import math
        assert math.isnan(result['a'].iloc[0])
        assert result['a'].iloc[1] == 0.5  # (150-100)/100 = 50%
        assert abs(result['a'].iloc[2] - (-0.2)) < 0.0001  # (120-150)/150 = -20%

    @pytest.mark.asyncio
    async def test_df_rank_default(self, interp):
        """Test DF.RANK with default options."""
        df = pd.DataFrame({'a': [3, 1, 2], 'b': [6, 4, 5]})
        interp.stack_push(df)
        await interp.run("pd.DF.RANK")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [3.0, 1.0, 2.0]
        assert result['b'].tolist() == [3.0, 1.0, 2.0]

    @pytest.mark.asyncio
    async def test_df_rank_descending(self, interp):
        """Test DF.RANK with ascending=False."""
        df = pd.DataFrame({'a': [3, 1, 2]})
        interp.stack_push(df)
        await interp.run("[.ascending FALSE] ~> pd.DF.RANK")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [1.0, 3.0, 2.0]

    @pytest.mark.asyncio
    async def test_df_rank_with_method(self, interp):
        """Test DF.RANK with custom method."""
        df = pd.DataFrame({'a': [1, 2, 2, 3]})
        interp.stack_push(df)
        await interp.run("[.method 'min'] ~> pd.DF.RANK")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        # With 'min' method, ties get the minimum rank
        assert result['a'].tolist() == [1.0, 2.0, 2.0, 4.0]


# ========================================
# Sorting & Filtering Operations
# ========================================


class TestSortingFilteringOperations:
    """Test DataFrame sorting and filtering operations."""

    @pytest.mark.asyncio
    async def test_df_sort_single_column(self, interp, sample_df):
        """Test DF.SORT with single column."""
        interp.stack_push(sample_df)
        await interp.run("'age' pd.DF.SORT")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result.iloc[0]['name'] == 'Bob'  # age 25
        assert result.iloc[1]['name'] == 'David'  # age 28
        assert result.iloc[2]['name'] == 'Alice'  # age 30
        assert result.iloc[3]['name'] == 'Charlie'  # age 35

    @pytest.mark.asyncio
    async def test_df_sort_descending(self, interp, sample_df):
        """Test DF.SORT with descending order."""
        interp.stack_push(sample_df)
        await interp.run("'age' [.ascending FALSE] ~> pd.DF.SORT")

        result = interp.stack_pop()
        assert result.iloc[0]['name'] == 'Charlie'  # age 35
        assert result.iloc[1]['name'] == 'Alice'  # age 30

    @pytest.mark.asyncio
    async def test_df_sort_multiple_columns(self, interp):
        """Test DF.SORT with multiple columns."""
        df = pd.DataFrame({
            'city': ['NYC', 'LA', 'NYC', 'LA'],
            'age': [30, 25, 28, 35]
        })
        interp.stack_push(df)
        await interp.run("['city' 'age'] pd.DF.SORT")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_df_sort_index(self, interp):
        """Test DF.SORT-INDEX."""
        df = pd.DataFrame({'a': [3, 1, 2]}, index=[2, 0, 1])
        interp.stack_push(df)
        await interp.run("pd.DF.SORT-INDEX")

        result = interp.stack_pop()
        assert result.index.tolist() == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_df_sort_index_descending(self, interp):
        """Test DF.SORT-INDEX with descending order."""
        df = pd.DataFrame({'a': [1, 2, 3]}, index=[0, 1, 2])
        interp.stack_push(df)
        await interp.run("[.ascending FALSE] ~> pd.DF.SORT-INDEX")

        result = interp.stack_pop()
        assert result.index.tolist() == [2, 1, 0]

    @pytest.mark.asyncio
    async def test_df_query(self, interp, sample_df):
        """Test DF.QUERY."""
        interp.stack_push(sample_df)
        await interp.run("'age > 28' pd.DF.QUERY")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]['name'] == 'Alice'
        assert result.iloc[1]['name'] == 'Charlie'

    @pytest.mark.asyncio
    async def test_df_query_complex(self, interp, sample_df):
        """Test DF.QUERY with complex expression."""
        interp.stack_push(sample_df)
        await interp.run("'age > 25 and city == \"NYC\"' pd.DF.QUERY")

        result = interp.stack_pop()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_df_isin(self, interp, sample_df):
        """Test DF.ISIN."""
        interp.stack_push(sample_df)
        await interp.run("'city' ['NYC' 'LA'] pd.DF.ISIN")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # Alice, Bob, Charlie

    @pytest.mark.asyncio
    async def test_df_isin_missing_column(self, interp, sample_df):
        """Test DF.ISIN raises error for missing column."""
        interp.stack_push(sample_df)

        with pytest.raises(KeyError, match="not found"):
            await interp.run("'invalid' ['value'] pd.DF.ISIN")

    @pytest.mark.asyncio
    async def test_df_dropna_default(self, interp):
        """Test DF.DROPNA with default options."""
        df = pd.DataFrame({'a': [1, 2, None], 'b': [4, None, 6]})
        interp.stack_push(df)
        await interp.run("pd.DF.DROPNA")

        result = interp.stack_pop()
        assert len(result) == 1  # Only first row has no NAs
        assert result.iloc[0]['a'] == 1

    @pytest.mark.asyncio
    async def test_df_dropna_all(self, interp):
        """Test DF.DROPNA with how='all'."""
        df = pd.DataFrame({'a': [1, None, None], 'b': [4, None, None]})
        interp.stack_push(df)
        await interp.run("[.how 'all'] ~> pd.DF.DROPNA")

        result = interp.stack_pop()
        assert len(result) == 1  # Only last row is all NAs

    @pytest.mark.asyncio
    async def test_df_dropna_subset(self, interp):
        """Test DF.DROPNA with subset option."""
        df = pd.DataFrame({'a': [1, 2, None], 'b': [4, None, 6]})
        interp.stack_push(df)
        await interp.run("[.subset ['a']] ~> pd.DF.DROPNA")

        result = interp.stack_pop()
        assert len(result) == 2  # Only drop rows with NA in column 'a'

    @pytest.mark.asyncio
    async def test_df_fillna_value(self, interp):
        """Test DF.FILLNA with value."""
        df = pd.DataFrame({'a': [1, None, 3], 'b': [4, 5, None]})
        interp.stack_push(df)
        await interp.run("0 pd.DF.FILLNA")

        result = interp.stack_pop()
        assert result['a'].tolist() == [1.0, 0.0, 3.0]
        assert result['b'].tolist() == [4.0, 5.0, 0.0]

    @pytest.mark.asyncio
    async def test_df_fillna_ffill(self, interp):
        """Test DF.FILLNA with forward fill."""
        df = pd.DataFrame({'a': [1, None, 3]})
        interp.stack_push(df)
        await interp.run("0 [.method 'ffill'] ~> pd.DF.FILLNA")

        result = interp.stack_pop()
        assert result['a'].tolist() == [1.0, 1.0, 3.0]

    @pytest.mark.asyncio
    async def test_df_duplicated_default(self, interp):
        """Test DF.DUPLICATED with default options."""
        df = pd.DataFrame({'a': [1, 2, 1, 3]})
        interp.stack_push(df)
        await interp.run("pd.DF.DUPLICATED")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result.tolist() == [False, False, True, False]

    @pytest.mark.asyncio
    async def test_df_duplicated_keep_last(self, interp):
        """Test DF.DUPLICATED with keep='last'."""
        df = pd.DataFrame({'a': [1, 2, 1, 3]})
        interp.stack_push(df)
        await interp.run("[.keep 'last'] ~> pd.DF.DUPLICATED")

        result = interp.stack_pop()
        assert result.tolist() == [True, False, False, False]

    @pytest.mark.asyncio
    async def test_df_duplicated_subset(self, interp):
        """Test DF.DUPLICATED with subset option."""
        df = pd.DataFrame({'a': [1, 1, 2], 'b': [3, 4, 3]})
        interp.stack_push(df)
        await interp.run("[.subset ['a']] ~> pd.DF.DUPLICATED")

        result = interp.stack_pop()
        assert result.tolist() == [False, True, False]


# ========================================
# File I/O Operations
# ========================================


class TestFileIOOperations:
    """Test DataFrame file I/O operations."""

    @pytest.mark.asyncio
    async def test_read_csv_and_to_csv(self, interp, tmp_path):
        """Test READ_CSV and TO_CSV."""
        # Create a CSV file
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df.to_csv(csv_file, index=False)

        # Read it with READ_CSV
        interp.stack_push(str(csv_file))
        await interp.run("pd.READ_CSV")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [1, 2, 3]
        assert result['b'].tolist() == [4, 5, 6]

        # Write it back with TO_CSV
        output_file = tmp_path / "output.csv"
        interp.stack_push(result)
        interp.stack_push(str(output_file))
        await interp.run("[.index FALSE] ~> pd.TO_CSV")

        # Verify the output file exists
        assert output_file.exists()

    @pytest.mark.asyncio
    async def test_read_csv_with_options(self, interp, tmp_path):
        """Test READ_CSV with custom separator."""
        # Create a TSV file
        tsv_file = tmp_path / "test.tsv"
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        df.to_csv(tsv_file, sep='\t', index=False)

        # Read it with custom separator
        interp.stack_push(str(tsv_file))
        await interp.run("[.sep '\t'] ~> pd.READ_CSV")

        result = interp.stack_pop()
        assert result['a'].tolist() == [1, 2]

    @pytest.mark.asyncio
    async def test_read_excel_and_to_excel(self, interp, tmp_path):
        """Test READ_EXCEL and TO_EXCEL."""
        # Create an Excel file
        excel_file = tmp_path / "test.xlsx"
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df.to_excel(excel_file, index=False)

        # Read it with READ_EXCEL
        interp.stack_push(str(excel_file))
        await interp.run("pd.READ_EXCEL")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [1, 2, 3]
        assert result['b'].tolist() == [4, 5, 6]

        # Write it back with TO_EXCEL
        output_file = tmp_path / "output.xlsx"
        interp.stack_push(result)
        interp.stack_push(str(output_file))
        await interp.run("[.index FALSE] ~> pd.TO_EXCEL")

        # Verify the output file exists
        assert output_file.exists()

    @pytest.mark.asyncio
    async def test_read_json_and_to_json(self, interp, tmp_path):
        """Test READ_JSON and TO_JSON."""
        # Create a JSON file
        json_file = tmp_path / "test.json"
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df.to_json(json_file, orient='records')

        # Read it with READ_JSON
        interp.stack_push(str(json_file))
        await interp.run("[.orient 'records'] ~> pd.READ_JSON")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [1, 2, 3]
        assert result['b'].tolist() == [4, 5, 6]

        # Write it back with TO_JSON
        output_file = tmp_path / "output.json"
        interp.stack_push(result)
        interp.stack_push(str(output_file))
        await interp.run("[.orient 'records' .indent 2] ~> pd.TO_JSON")

        # Verify the output file exists
        assert output_file.exists()

    @pytest.mark.asyncio
    async def test_to_csv_with_custom_options(self, interp, tmp_path):
        """Test TO_CSV with custom options."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        output_file = tmp_path / "custom.csv"

        interp.stack_push(df)
        interp.stack_push(str(output_file))
        await interp.run("[.sep ';' .header FALSE .index FALSE] ~> pd.TO_CSV")

        # Read the file and verify
        content = output_file.read_text()
        assert ';' in content
        assert 'a' not in content  # No header

    @pytest.mark.asyncio
    async def test_read_excel_with_sheet_name(self, interp, tmp_path):
        """Test READ_EXCEL with specific sheet name."""
        excel_file = tmp_path / "multi_sheet.xlsx"

        # Create Excel file with multiple sheets
        with pd.ExcelWriter(excel_file) as writer:
            df1 = pd.DataFrame({'a': [1, 2]})
            df2 = pd.DataFrame({'b': [3, 4]})
            df1.to_excel(writer, sheet_name='Sheet1', index=False)
            df2.to_excel(writer, sheet_name='Sheet2', index=False)

        # Read specific sheet
        interp.stack_push(str(excel_file))
        await interp.run("[.sheet_name 'Sheet2'] ~> pd.READ_EXCEL")

        result = interp.stack_pop()
        assert 'b' in result.columns
        assert 'a' not in result.columns


# ========================================
# Transformation Operations
# ========================================


class TestTransformationOperations:
    """Test DataFrame transformation operations."""

    @pytest.mark.asyncio
    async def test_df_map(self, interp):
        """Test DF.MAP applies Forthic to all elements."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("'2 *' pd.DF.MAP")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result['a'].tolist() == [2, 4, 6]
        assert result['b'].tolist() == [8, 10, 12]

    @pytest.mark.asyncio
    async def test_df_apply_to_rows(self, interp, sample_df):
        """Test DF.APPLY with axis=1 (rows)."""
        interp.stack_push(sample_df)
        await interp.run("'\"age\" REC@' [.axis 1] ~> pd.DF.APPLY")

        result = interp.stack_pop()
        assert isinstance(result, pd.Series)
        assert result.tolist() == [30, 25, 35, 28]

    @pytest.mark.asyncio
    async def test_df_transform(self, interp):
        """Test DF.TRANSFORM with function name."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        interp.stack_push(df)
        await interp.run("'sqrt' pd.DF.TRANSFORM")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        import math
        assert abs(result['a'].iloc[0] - 1.0) < 0.01
        assert abs(result['a'].iloc[1] - math.sqrt(2)) < 0.01

    @pytest.mark.asyncio
    async def test_df_reset_index(self, interp):
        """Test DF.RESET-INDEX."""
        df = pd.DataFrame({'a': [1, 2, 3]}, index=[10, 20, 30])
        interp.stack_push(df)
        await interp.run("pd.DF.RESET-INDEX")

        result = interp.stack_pop()
        assert result.index.tolist() == [0, 1, 2]
        assert 'index' in result.columns  # Old index becomes column

    @pytest.mark.asyncio
    async def test_df_reset_index_drop(self, interp):
        """Test DF.RESET-INDEX with drop=True."""
        df = pd.DataFrame({'a': [1, 2, 3]}, index=[10, 20, 30])
        interp.stack_push(df)
        await interp.run("[.drop TRUE] ~> pd.DF.RESET-INDEX")

        result = interp.stack_pop()
        assert result.index.tolist() == [0, 1, 2]
        assert 'index' not in result.columns  # Old index dropped

    @pytest.mark.asyncio
    async def test_df_set_index(self, interp, sample_df):
        """Test DF.SET-INDEX."""
        interp.stack_push(sample_df)
        await interp.run("'name' pd.DF.SET-INDEX")

        result = interp.stack_pop()
        assert result.index.tolist() == ['Alice', 'Bob', 'Charlie', 'David']
        assert 'name' not in result.columns  # Name column dropped

    @pytest.mark.asyncio
    async def test_df_set_index_no_drop(self, interp, sample_df):
        """Test DF.SET-INDEX with drop=False."""
        interp.stack_push(sample_df)
        await interp.run("'name' [.drop FALSE] ~> pd.DF.SET-INDEX")

        result = interp.stack_pop()
        assert 'name' in result.columns  # Name column kept

    @pytest.mark.asyncio
    async def test_df_transpose(self, interp):
        """Test DF.TRANSPOSE."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        interp.stack_push(df)
        await interp.run("pd.DF.TRANSPOSE")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)  # Swapped dimensions

    @pytest.mark.asyncio
    async def test_df_melt(self, interp):
        """Test DF.MELT."""
        df = pd.DataFrame({'id': [1, 2], 'a': [10, 20], 'b': [30, 40]})
        interp.stack_push(df)
        await interp.run("[.id_vars ['id'] .value_vars ['a' 'b']] ~> pd.DF.MELT")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4  # 2 rows * 2 value columns
        assert 'variable' in result.columns
        assert 'value' in result.columns

    @pytest.mark.asyncio
    async def test_df_explode(self, interp):
        """Test DF.EXPLODE."""
        df = pd.DataFrame({'a': [[1, 2], [3, 4]], 'b': [10, 20]})
        interp.stack_push(df)
        await interp.run("'a' pd.DF.EXPLODE")

        result = interp.stack_pop()
        assert len(result) == 4  # Exploded from 2 to 4 rows
        assert result['a'].tolist() == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_df_replace(self, interp):
        """Test DF.REPLACE."""
        df = pd.DataFrame({'a': [1, 2, 3, 1]})
        interp.stack_push(df)
        await interp.run("1 99 pd.DF.REPLACE")

        result = interp.stack_pop()
        assert result['a'].tolist() == [99, 2, 3, 99]


# ========================================
# Merge & Join Operations
# ========================================


class TestMergeJoinOperations:
    """Test DataFrame merge and join operations."""

    @pytest.mark.asyncio
    async def test_df_merge_inner(self, interp):
        """Test DF.MERGE with inner join."""
        df1 = pd.DataFrame({'key': ['a', 'b', 'c'], 'val1': [1, 2, 3]})
        df2 = pd.DataFrame({'key': ['a', 'b', 'd'], 'val2': [4, 5, 6]})

        interp.stack_push(df1)
        interp.stack_push(df2)
        await interp.run("[.on 'key' .how 'inner'] ~> pd.DF.MERGE")

        result = interp.stack_pop()
        assert len(result) == 2  # Only a and b match
        assert 'val1' in result.columns
        assert 'val2' in result.columns

    @pytest.mark.asyncio
    async def test_df_merge_left(self, interp):
        """Test DF.MERGE with left join."""
        df1 = pd.DataFrame({'key': ['a', 'b', 'c'], 'val1': [1, 2, 3]})
        df2 = pd.DataFrame({'key': ['a', 'b'], 'val2': [4, 5]})

        interp.stack_push(df1)
        interp.stack_push(df2)
        await interp.run("[.on 'key' .how 'left'] ~> pd.DF.MERGE")

        result = interp.stack_pop()
        assert len(result) == 3  # All from left
        assert result['key'].tolist() == ['a', 'b', 'c']

    @pytest.mark.asyncio
    async def test_df_join(self, interp):
        """Test DF.JOIN."""
        df1 = pd.DataFrame({'a': [1, 2, 3]}, index=['x', 'y', 'z'])
        df2 = pd.DataFrame({'b': [4, 5, 6]}, index=['x', 'y', 'z'])

        interp.stack_push(df1)
        interp.stack_push(df2)
        await interp.run("pd.DF.JOIN")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert 'a' in result.columns
        assert 'b' in result.columns

    @pytest.mark.asyncio
    async def test_df_concat_rows(self, interp):
        """Test DF.CONCAT along rows (axis=0)."""
        df1 = pd.DataFrame({'a': [1, 2]})
        df2 = pd.DataFrame({'a': [3, 4]})

        interp.stack_push([df1, df2])
        await interp.run("pd.DF.CONCAT")

        result = interp.stack_pop()
        assert len(result) == 4
        assert result['a'].tolist() == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_df_concat_columns(self, interp):
        """Test DF.CONCAT along columns (axis=1)."""
        df1 = pd.DataFrame({'a': [1, 2]})
        df2 = pd.DataFrame({'b': [3, 4]})

        interp.stack_push([df1, df2])
        await interp.run("[.axis 1] ~> pd.DF.CONCAT")

        result = interp.stack_pop()
        assert list(result.columns) == ['a', 'b']


# ========================================
# String Operations
# ========================================


class TestStringOperations:
    """Test Series string operations."""

    @pytest.mark.asyncio
    async def test_str_upper(self, interp):
        """Test STR.UPPER."""
        series = pd.Series(['hello', 'world'])
        interp.stack_push(series)
        await interp.run("pd.STR.UPPER")

        result = interp.stack_pop()
        assert result.tolist() == ['HELLO', 'WORLD']

    @pytest.mark.asyncio
    async def test_str_lower(self, interp):
        """Test STR.LOWER."""
        series = pd.Series(['HELLO', 'WORLD'])
        interp.stack_push(series)
        await interp.run("pd.STR.LOWER")

        result = interp.stack_pop()
        assert result.tolist() == ['hello', 'world']

    @pytest.mark.asyncio
    async def test_str_strip(self, interp):
        """Test STR.STRIP."""
        series = pd.Series(['  hello  ', '  world  '])
        interp.stack_push(series)
        await interp.run("pd.STR.STRIP")

        result = interp.stack_pop()
        assert result.tolist() == ['hello', 'world']

    @pytest.mark.asyncio
    async def test_str_contains(self, interp):
        """Test STR.CONTAINS."""
        series = pd.Series(['apple', 'banana', 'cherry'])
        interp.stack_push(series)
        await interp.run("'an' pd.STR.CONTAINS")

        result = interp.stack_pop()
        assert result.tolist() == [False, True, False]

    @pytest.mark.asyncio
    async def test_str_contains_case_insensitive(self, interp):
        """Test STR.CONTAINS with case=False."""
        series = pd.Series(['Apple', 'Banana'])
        interp.stack_push(series)
        await interp.run("'APP' [.case FALSE] ~> pd.STR.CONTAINS")

        result = interp.stack_pop()
        assert result.tolist() == [True, False]

    @pytest.mark.asyncio
    async def test_str_split(self, interp):
        """Test STR.SPLIT."""
        series = pd.Series(['a,b,c', 'd,e,f'])
        interp.stack_push(series)
        await interp.run("',' pd.STR.SPLIT")

        result = interp.stack_pop()
        assert result.tolist() == [['a', 'b', 'c'], ['d', 'e', 'f']]

    @pytest.mark.asyncio
    async def test_str_replace(self, interp):
        """Test STR.REPLACE."""
        series = pd.Series(['hello world', 'goodbye world'])
        interp.stack_push(series)
        await interp.run("'world' 'there' pd.STR.REPLACE")

        result = interp.stack_pop()
        assert result.tolist() == ['hello there', 'goodbye there']

    @pytest.mark.asyncio
    async def test_str_extract(self, interp):
        """Test STR.EXTRACT."""
        series = pd.Series(['a1', 'b2', 'c3'])
        interp.stack_push(series)
        await interp.run("'([a-z])([0-9])' pd.STR.EXTRACT")

        result = interp.stack_pop()
        assert isinstance(result, pd.DataFrame)
        assert result[0].tolist() == ['a', 'b', 'c']
        assert result[1].tolist() == ['1', '2', '3']
