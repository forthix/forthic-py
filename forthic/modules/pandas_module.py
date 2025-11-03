"""Pandas module - DataFrame and Series operations for data manipulation.

Provides comprehensive pandas integration for Forthic including:
- DataFrame/Series conversion
- Data inspection and exploration
- Column and row operations
- Aggregation and grouping
- File I/O operations
"""

from __future__ import annotations

from typing import Any

try:
    import pandas as pd
except ImportError:
    raise ImportError(
        "Pandas module requires pandas to be installed. "
        "Install with: pip install 'forthic[pandas]' or pip install pandas"
    )

from ..decorators import DecoratedModule, ForthicDirectWord, register_module_doc
from ..decorators import ForthicWord as WordDecorator


class PandasModule(DecoratedModule):
    """Pandas DataFrame and Series operations for data manipulation and analysis."""

    def __init__(self):
        super().__init__("pandas")
        register_module_doc(
            PandasModule,
            """
Pandas DataFrame and Series operations for data manipulation and analysis.

## Categories
- Conversion: >DF, DF>, >SERIES, SERIES>
- Inspection: DF.INFO, DF.HEAD, DF.TAIL, DF.SHAPE, DF.COLUMNS, DF.DTYPES, DF.DESCRIBE, DF.NUNIQUE

## Options
Several words support options via the ~> operator using syntax: [.option_name value ...] ~> WORD
- index: Series/DataFrame index (list)
- name: Series name (str)
- n: Number of rows (int)

## Examples
# Create DataFrame from records
[
    [['name' 'Alice'] ['age' 30]] REC
    [['name' 'Bob'] ['age' 25]] REC
] >DF

# Inspect data
DF.HEAD DF.INFO

# Convert back to records
DF>
            """,
        )

    # ==================
    # Conversion Operations
    # ==================

    @WordDecorator("( records:list -- df:DataFrame )", "Convert list of records to DataFrame", ">DF")
    async def to_DF(self, records: list) -> pd.DataFrame:
        """Convert list of records (dicts) to DataFrame."""
        if records is None or len(records) == 0:
            return pd.DataFrame()
        return pd.DataFrame(records)

    @WordDecorator("( df:DataFrame -- records:list )", "Convert DataFrame to list of records", "DF>")
    async def DF_to(self, df: pd.DataFrame) -> list:
        """Convert DataFrame to list of records."""
        if df is None or df.empty:
            return []
        return df.to_dict("records")

    @WordDecorator(
        "( values:list [options:WordOptions] -- series:Series )",
        "Convert list to Series with optional index and name",
        ">SERIES",
    )
    async def to_SERIES(self, values: list, options: dict[str, Any]) -> pd.Series:
        """Convert list to Series with optional index and name.

        Options:
            index: list - Index for the Series
            name: str - Name for the Series
        """
        if values is None:
            values = []

        index = options.get("index")
        name = options.get("name")

        return pd.Series(values, index=index, name=name)

    @WordDecorator("( series:Series -- values:list )", "Convert Series to list of values", "SERIES>")
    async def SERIES_to(self, series: pd.Series) -> list:
        """Convert Series to list of values."""
        if series is None or series.empty:
            return []
        return series.tolist()

    # ==================
    # Inspection Operations
    # ==================

    @WordDecorator(
        "( df:DataFrame -- df:DataFrame )",
        "Print DataFrame info to stdout, return df for chaining",
        "DF.INFO",
    )
    async def DF_INFO(self, df: pd.DataFrame) -> pd.DataFrame:
        """Print DataFrame info and return df for chaining."""
        if df is None:
            print("None")
            return pd.DataFrame()

        df.info()
        return df

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Get first n rows (default 5)",
        "DF.HEAD",
    )
    async def DF_HEAD(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Get first n rows (default 5)."""
        if df is None:
            return pd.DataFrame()

        n = options.get("n", 5)
        return df.head(n)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Get last n rows (default 5)",
        "DF.TAIL",
    )
    async def DF_TAIL(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Get last n rows (default 5)."""
        if df is None:
            return pd.DataFrame()

        n = options.get("n", 5)
        return df.tail(n)

    @WordDecorator("( df:DataFrame -- shape:list )", "Get DataFrame shape as [rows, cols]", "DF.SHAPE")
    async def DF_SHAPE(self, df: pd.DataFrame) -> list:
        """Get DataFrame shape as [rows, cols]."""
        if df is None:
            return [0, 0]
        return list(df.shape)

    @WordDecorator("( df:DataFrame -- columns:list )", "Get list of column names", "DF.COLUMNS")
    async def DF_COLUMNS(self, df: pd.DataFrame) -> list:
        """Get list of column names."""
        if df is None:
            return []
        return df.columns.tolist()

    @WordDecorator("( df:DataFrame -- dtypes:dict )", "Get column data types as dict {col: dtype}", "DF.DTYPES")
    async def DF_DTYPES(self, df: pd.DataFrame) -> dict:
        """Get column data types as dict."""
        if df is None:
            return {}
        return df.dtypes.astype(str).to_dict()

    @WordDecorator("( df:DataFrame -- stats:DataFrame )", "Get summary statistics", "DF.DESCRIBE")
    async def DF_DESCRIBE(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get summary statistics."""
        if df is None:
            return pd.DataFrame()
        return df.describe()

    @WordDecorator("( df:DataFrame -- counts:dict )", "Count unique values per column", "DF.NUNIQUE")
    async def DF_NUNIQUE(self, df: pd.DataFrame) -> dict:
        """Count unique values per column."""
        if df is None:
            return {}
        return df.nunique().to_dict()

    # ==================
    # Column Operations
    # ==================

    @WordDecorator("( df:DataFrame column:str -- series:Series )", "Get column by name", "DF@")
    async def DF_at(self, df: pd.DataFrame, column: str) -> pd.Series:
        """Get single column as Series."""
        if df is None or df.empty:
            return pd.Series()
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")
        return df[column]

    @WordDecorator("( df:DataFrame columns:list -- df:DataFrame )", "Get multiple columns as DataFrame", "DF@@")
    async def DF_at_at(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """Get multiple columns as DataFrame."""
        if df is None or df.empty:
            return pd.DataFrame()
        if not columns:
            return pd.DataFrame()
        missing = [col for col in columns if col not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in DataFrame: {missing}")
        return df[columns]

    @WordDecorator(
        "( df:DataFrame series:Series column:str -- df:DataFrame )",
        "Set or add column to DataFrame",
        "<DF!",
    )
    async def l_DF_bang(self, df: pd.DataFrame, series: pd.Series, column: str) -> pd.DataFrame:
        """Set or add column to DataFrame (returns new DataFrame)."""
        if df is None:
            df = pd.DataFrame()

        # Handle both Series and list/array-like inputs
        if isinstance(series, pd.Series):
            return df.assign(**{column: series})
        else:
            return df.assign(**{column: pd.Series(series)})

    @WordDecorator("( df:DataFrame columns:list -- df:DataFrame )", "Drop columns from DataFrame", "DF.DROP-COLS")
    async def DF_DROP_COLS(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """Drop columns from DataFrame."""
        if df is None or df.empty:
            return pd.DataFrame()
        if not columns:
            return df
        # Only drop columns that exist
        to_drop = [col for col in columns if col in df.columns]
        if not to_drop:
            return df
        return df.drop(columns=to_drop)

    @WordDecorator(
        "( df:DataFrame mapping:dict -- df:DataFrame )",
        "Rename columns using dict mapping",
        "DF.RENAME-COLS",
    )
    async def DF_RENAME_COLS(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """Rename columns using dict mapping {old_name: new_name}."""
        if df is None or df.empty:
            return pd.DataFrame()
        if not mapping:
            return df
        return df.rename(columns=mapping)

    @WordDecorator(
        "( df:DataFrame dtypes:any -- df:DataFrame )",
        "Select columns by data type(s)",
        "DF.SELECT-DTYPES",
    )
    async def DF_SELECT_DTYPES(self, df: pd.DataFrame, dtypes: Any) -> pd.DataFrame:
        """Select columns by data type(s).

        Args:
            dtypes: Single dtype string or list of dtype strings
                    (e.g., 'number', 'object', ['int64', 'float64'])
        """
        if df is None or df.empty:
            return pd.DataFrame()

        # Handle both single dtype and list of dtypes
        if isinstance(dtypes, str):
            dtypes = [dtypes]

        return df.select_dtypes(include=dtypes)

    @ForthicDirectWord("( df:DataFrame column:str forthic:str -- series:Series )", "Apply Forthic to column", "DF.APPLY-COL")
    async def DF_APPLY_COL(self, interp) -> None:
        """Apply Forthic code to each value in a column.

        The Forthic code receives each column value on the stack and should
        leave a transformed value on the stack.
        """
        forthic = interp.stack_pop()
        column = interp.stack_pop()
        df = interp.stack_pop()

        if df is None or df.empty:
            interp.stack_push(pd.Series())
            return

        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")

        string_location = interp.get_string_location()
        result = []

        for value in df[column]:
            interp.stack_push(value)
            await interp.run(forthic, string_location)
            result.append(interp.stack_pop())

        interp.stack_push(pd.Series(result, index=df.index, name=column))

    @WordDecorator(
        "( df:DataFrame column:str dtype:str -- df:DataFrame )",
        "Convert column to specified dtype",
        "DF.ASTYPE",
    )
    async def DF_ASTYPE(self, df: pd.DataFrame, column: str, dtype: str) -> pd.DataFrame:
        """Convert column to specified dtype.

        Args:
            column: Column name to convert
            dtype: Target dtype (e.g., 'int', 'float', 'str', 'bool')
        """
        if df is None or df.empty:
            return pd.DataFrame()

        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")

        return df.assign(**{column: df[column].astype(dtype)})

    # ==================
    # Row Operations
    # ==================

    @WordDecorator("( df:DataFrame index:int -- record:dict )", "Get row by position as record", "DF.ILOC")
    async def DF_ILOC(self, df: pd.DataFrame, index: int) -> dict:
        """Get row by position (integer index) as record."""
        if df is None or df.empty:
            return {}
        if index < 0 or index >= len(df):
            raise IndexError(f"Row index {index} out of range for DataFrame with {len(df)} rows")
        return df.iloc[index].to_dict()

    @WordDecorator("( df:DataFrame label:any -- record:dict )", "Get row by label as record", "DF.LOC")
    async def DF_LOC(self, df: pd.DataFrame, label: Any) -> dict:
        """Get row by label (index value) as record."""
        if df is None or df.empty:
            return {}
        if label not in df.index:
            raise KeyError(f"Label '{label}' not found in DataFrame index")
        return df.loc[label].to_dict()

    @ForthicDirectWord("( df:DataFrame forthic:str -- df:DataFrame )", "Filter rows with Forthic predicate", "DF.FILTER")
    async def DF_FILTER(self, interp) -> None:
        """Filter DataFrame rows using Forthic predicate.

        The Forthic code receives each row as a record (dict) on the stack
        and should leave a boolean value indicating whether to keep the row.
        """
        forthic = interp.stack_pop()
        df = interp.stack_pop()

        if df is None or df.empty:
            interp.stack_push(pd.DataFrame())
            return

        string_location = interp.get_string_location()
        mask = []

        for _, row in df.iterrows():
            row_dict = row.to_dict()
            interp.stack_push(row_dict)
            await interp.run(forthic, string_location)
            mask.append(bool(interp.stack_pop()))

        result = df[mask]
        interp.stack_push(result)

    @WordDecorator("( df:DataFrame indices:list -- df:DataFrame )", "Drop rows by index", "DF.DROP-ROWS")
    async def DF_DROP_ROWS(self, df: pd.DataFrame, indices: list) -> pd.DataFrame:
        """Drop rows by index labels."""
        if df is None or df.empty:
            return pd.DataFrame()
        if not indices:
            return df
        # Only drop indices that exist
        to_drop = [idx for idx in indices if idx in df.index]
        if not to_drop:
            return df
        return df.drop(index=to_drop)

    @WordDecorator("( df:DataFrame row:dict -- df:DataFrame )", "Append single row to DataFrame", "DF.APPEND-ROW")
    async def DF_APPEND_ROW(self, df: pd.DataFrame, row: dict) -> pd.DataFrame:
        """Append a single row (record) to DataFrame."""
        if df is None:
            df = pd.DataFrame()

        if not row:
            return df

        # Use pd.concat for modern pandas (append is deprecated)
        new_row_df = pd.DataFrame([row])
        return pd.concat([df, new_row_df], ignore_index=True)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Random sample of rows with optional parameters",
        "DF.SAMPLE",
    )
    async def DF_SAMPLE(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Random sample of rows.

        Options:
            n: Number of rows to sample (default: 1)
            frac: Fraction of rows to sample (alternative to n)
            random_state: Seed for reproducibility
        """
        if df is None or df.empty:
            return pd.DataFrame()

        n = options.get("n")
        frac = options.get("frac")
        random_state = options.get("random_state")

        # Default to n=1 if neither n nor frac specified
        if n is None and frac is None:
            n = 1

        return df.sample(n=n, frac=frac, random_state=random_state)

    @WordDecorator(
        "( df:DataFrame column:str n:int -- df:DataFrame )",
        "Get top N rows by column values",
        "DF.NLARGEST",
    )
    async def DF_NLARGEST(self, df: pd.DataFrame, column: str, n: int) -> pd.DataFrame:
        """Get top N rows by column values."""
        if df is None or df.empty:
            return pd.DataFrame()
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")
        return df.nlargest(n, column)

    # ==================
    # Aggregation Operations
    # ==================

    @WordDecorator(
        "( df:DataFrame columns:any -- grouped:DataFrameGroupBy )",
        "Group DataFrame by column(s)",
        "DF.GROUP-BY",
    )
    async def DF_GROUP_BY(self, df: pd.DataFrame, columns: Any) -> Any:
        """Group DataFrame by column(s).

        Args:
            columns: Single column name or list of column names
        """
        if df is None or df.empty:
            return df.groupby([])

        # Handle both single column and list of columns
        return df.groupby(columns)

    @WordDecorator(
        "( df_or_grouped:any agg_spec:any -- df:DataFrame )",
        "Aggregate using function name or dict",
        "DF.AGG",
    )
    async def DF_AGG(self, obj: Any, agg_spec: Any) -> pd.DataFrame:
        """Aggregate using function or dict of {column: function}.

        Args:
            obj: DataFrame or GroupBy object
            agg_spec: Function name string (e.g., 'sum', 'mean') or dict
        """
        if obj is None:
            return pd.DataFrame()

        result = obj.agg(agg_spec)

        # If result is a Series, convert to DataFrame for consistency
        if isinstance(result, pd.Series):
            return result.to_frame()

        return result

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- result:any )",
        "Sum values with optional axis",
        "DF.SUM",
    )
    async def DF_SUM(self, df: pd.DataFrame, options: dict[str, Any]) -> Any:
        """Sum values.

        Options:
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.Series()

        axis = options.get("axis", 0)
        return df.sum(axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- result:any )",
        "Mean values with optional axis",
        "DF.MEAN",
    )
    async def DF_MEAN(self, df: pd.DataFrame, options: dict[str, Any]) -> Any:
        """Mean values.

        Options:
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.Series()

        axis = options.get("axis", 0)
        return df.mean(axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- result:any )",
        "Median values with optional axis",
        "DF.MEDIAN",
    )
    async def DF_MEDIAN(self, df: pd.DataFrame, options: dict[str, Any]) -> Any:
        """Median values.

        Options:
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.Series()

        axis = options.get("axis", 0)
        return df.median(axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- result:any )",
        "Count non-NA values with optional axis",
        "DF.COUNT",
    )
    async def DF_COUNT(self, df: pd.DataFrame, options: dict[str, Any]) -> Any:
        """Count non-NA values.

        Options:
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.Series()

        axis = options.get("axis", 0)
        return df.count(axis=axis)

    @WordDecorator(
        "( series:Series -- counts:Series )",
        "Count unique values in Series",
        "DF.VALUE-COUNTS",
    )
    async def DF_VALUE_COUNTS(self, series: pd.Series) -> pd.Series:
        """Count unique values in Series."""
        if series is None or series.empty:
            return pd.Series()

        return series.value_counts()

    @WordDecorator(
        "( df:DataFrame values:str index:str [options:WordOptions] -- df:DataFrame )",
        "Create pivot table",
        "DF.PIVOT",
    )
    async def DF_PIVOT(self, df: pd.DataFrame, values: str, index: str, options: dict[str, Any]) -> pd.DataFrame:
        """Create pivot table.

        Options:
            columns: Column to use for pivot columns
        """
        if df is None or df.empty:
            return pd.DataFrame()

        columns = options.get("columns")
        return df.pivot(index=index, columns=columns, values=values)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Create advanced pivot table with aggregation",
        "DF.PIVOT-TABLE",
    )
    async def DF_PIVOT_TABLE(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Create advanced pivot table.

        Options:
            values: Column to aggregate
            index: Column(s) for index
            columns: Column(s) for columns
            aggfunc: Aggregation function (default: 'mean')
        """
        if df is None or df.empty:
            return pd.DataFrame()

        values = options.get("values")
        index = options.get("index")
        columns = options.get("columns")
        aggfunc = options.get("aggfunc", "mean")

        return pd.pivot_table(df, values=values, index=index, columns=columns, aggfunc=aggfunc)

    @WordDecorator(
        "( index:any columns:any [options:WordOptions] -- df:DataFrame )",
        "Compute cross-tabulation of two factors",
        "DF.CROSSTAB",
    )
    async def DF_CROSSTAB(self, index: Any, columns: Any, options: dict[str, Any]) -> pd.DataFrame:
        """Compute cross-tabulation.

        Options:
            normalize: Normalize by 'all', 'index', 'columns', or False (default)
        """
        normalize = options.get("normalize", False)
        return pd.crosstab(index, columns, normalize=normalize)

    # ==================
    # Statistical Operations
    # ==================

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Compute correlation matrix",
        "DF.CORR",
    )
    async def DF_CORR(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Compute pairwise correlation of columns.

        Options:
            method: 'pearson' (default), 'kendall', or 'spearman'
        """
        if df is None or df.empty:
            return pd.DataFrame()

        method = options.get("method", "pearson")
        return df.corr(method=method)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Compute covariance matrix",
        "DF.COV",
    )
    async def DF_COV(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Compute pairwise covariance of columns."""
        if df is None or df.empty:
            return pd.DataFrame()

        return df.cov()

    @WordDecorator(
        "( df:DataFrame window:int [options:WordOptions] -- rolling:Rolling )",
        "Create rolling window object",
        "DF.ROLLING",
    )
    async def DF_ROLLING(self, df: pd.DataFrame, window: int, options: dict[str, Any]) -> Any:
        """Create rolling window object.

        Options:
            min_periods: Minimum number of observations in window
        """
        if df is None or df.empty:
            return df.rolling(window=0)

        min_periods = options.get("min_periods")
        return df.rolling(window=window, min_periods=min_periods)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Cumulative sum",
        "DF.CUMSUM",
    )
    async def DF_CUMSUM(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Cumulative sum over DataFrame axis.

        Options:
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.DataFrame()

        axis = options.get("axis", 0)
        return df.cumsum(axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Cumulative product",
        "DF.CUMPROD",
    )
    async def DF_CUMPROD(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Cumulative product over DataFrame axis.

        Options:
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.DataFrame()

        axis = options.get("axis", 0)
        return df.cumprod(axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "First discrete difference",
        "DF.DIFF",
    )
    async def DF_DIFF(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Calculate first discrete difference.

        Options:
            periods: Number of periods to shift (default: 1)
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.DataFrame()

        periods = options.get("periods", 1)
        axis = options.get("axis", 0)
        return df.diff(periods=periods, axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Percentage change between current and prior element",
        "DF.PCT-CHANGE",
    )
    async def DF_PCT_CHANGE(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Calculate percentage change.

        Options:
            periods: Number of periods to shift (default: 1)
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.DataFrame()

        periods = options.get("periods", 1)
        axis = options.get("axis", 0)
        return df.pct_change(periods=periods, axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Rank values along axis",
        "DF.RANK",
    )
    async def DF_RANK(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Compute numerical data ranks along axis.

        Options:
            method: 'average' (default), 'min', 'max', 'first', 'dense'
            ascending: True (default) or False
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.DataFrame()

        method = options.get("method", "average")
        ascending = options.get("ascending", True)
        axis = options.get("axis", 0)
        return df.rank(method=method, ascending=ascending, axis=axis)

    # ==================
    # Sorting & Filtering Operations
    # ==================

    @WordDecorator(
        "( df:DataFrame by:any [options:WordOptions] -- df:DataFrame )",
        "Sort DataFrame by column(s)",
        "DF.SORT",
    )
    async def DF_SORT(self, df: pd.DataFrame, by: Any, options: dict[str, Any]) -> pd.DataFrame:
        """Sort DataFrame by column(s).

        Options:
            ascending: True (default) or False, or list for multiple columns
        """
        if df is None or df.empty:
            return pd.DataFrame()

        ascending = options.get("ascending", True)
        return df.sort_values(by=by, ascending=ascending)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Sort DataFrame by index",
        "DF.SORT-INDEX",
    )
    async def DF_SORT_INDEX(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Sort DataFrame by index.

        Options:
            ascending: True (default) or False
        """
        if df is None or df.empty:
            return pd.DataFrame()

        ascending = options.get("ascending", True)
        return df.sort_index(ascending=ascending)

    @WordDecorator(
        "( df:DataFrame query_str:str -- df:DataFrame )",
        "Query DataFrame with pandas expression",
        "DF.QUERY",
    )
    async def DF_QUERY(self, df: pd.DataFrame, query_str: str) -> pd.DataFrame:
        """Query DataFrame using pandas expression string.

        Example: "age > 30 and city == 'NYC'"
        """
        if df is None or df.empty:
            return pd.DataFrame()

        return df.query(query_str)

    @WordDecorator(
        "( df:DataFrame column:str values:list -- df:DataFrame )",
        "Filter rows where column value is in values list",
        "DF.ISIN",
    )
    async def DF_ISIN(self, df: pd.DataFrame, column: str, values: list) -> pd.DataFrame:
        """Filter DataFrame to rows where column value is in values list."""
        if df is None or df.empty:
            return pd.DataFrame()

        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")

        return df[df[column].isin(values)]

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Drop rows with NA values",
        "DF.DROPNA",
    )
    async def DF_DROPNA(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Drop rows with NA values.

        Options:
            how: 'any' (default) or 'all'
            subset: List of column names to consider
        """
        if df is None or df.empty:
            return pd.DataFrame()

        how = options.get("how", "any")
        subset = options.get("subset")
        return df.dropna(how=how, subset=subset)

    @WordDecorator(
        "( df:DataFrame value:any [options:WordOptions] -- df:DataFrame )",
        "Fill NA values with specified value",
        "DF.FILLNA",
    )
    async def DF_FILLNA(self, df: pd.DataFrame, value: Any, options: dict[str, Any]) -> pd.DataFrame:
        """Fill NA values with specified value.

        Options:
            method: 'ffill' or 'bfill' for forward/backward fill
        """
        if df is None or df.empty:
            return pd.DataFrame()

        method = options.get("method")
        if method:
            # Use new pandas API: df.ffill() or df.bfill() instead of fillna(method=...)
            if method == "ffill":
                return df.ffill()
            elif method == "bfill":
                return df.bfill()
            else:
                raise ValueError(f"Invalid method: {method}. Use 'ffill' or 'bfill'")
        else:
            return df.fillna(value)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- result:any )",
        "Find duplicate rows",
        "DF.DUPLICATED",
    )
    async def DF_DUPLICATED(self, df: pd.DataFrame, options: dict[str, Any]) -> Any:
        """Find duplicate rows.

        Options:
            subset: List of column names to consider
            keep: 'first' (default), 'last', or False
        """
        if df is None or df.empty:
            return pd.Series(dtype=bool)

        subset = options.get("subset")
        keep = options.get("keep", "first")
        return df.duplicated(subset=subset, keep=keep)

    # ==================
    # File I/O Operations
    # ==================

    @WordDecorator(
        "( filepath:str [options:WordOptions] -- df:DataFrame )",
        "Read CSV file into DataFrame",
        "READ_CSV",
    )
    async def READ_CSV(self, filepath: str, options: dict[str, Any]) -> pd.DataFrame:
        """Read CSV file into DataFrame.

        Options:
            sep: Delimiter (default: ',')
            header: Row number to use as column names (default: 0)
            index_col: Column to use as row labels
            dtype: Dict of column names to data types
        """
        return pd.read_csv(filepath, **options)

    @WordDecorator(
        "( filepath:str [options:WordOptions] -- df:DataFrame )",
        "Read Excel file into DataFrame",
        "READ_EXCEL",
    )
    async def READ_EXCEL(self, filepath: str, options: dict[str, Any]) -> pd.DataFrame:
        """Read Excel file into DataFrame.

        Options:
            sheet_name: Sheet name or index (default: 0)
            header: Row number to use as column names (default: 0)
            index_col: Column to use as row labels
        """
        return pd.read_excel(filepath, **options)

    @WordDecorator(
        "( filepath:str [options:WordOptions] -- df:DataFrame )",
        "Read JSON file into DataFrame",
        "READ_JSON",
    )
    async def READ_JSON(self, filepath: str, options: dict[str, Any]) -> pd.DataFrame:
        """Read JSON file into DataFrame.

        Options:
            orient: 'records', 'index', 'columns', etc.
        """
        return pd.read_json(filepath, **options)

    @WordDecorator(
        "( df:DataFrame filepath:str [options:WordOptions] -- )",
        "Write DataFrame to CSV file",
        "TO_CSV",
    )
    async def TO_CSV(self, df: pd.DataFrame, filepath: str, options: dict[str, Any]) -> None:
        """Write DataFrame to CSV file.

        Options:
            index: Whether to write row index (default: True)
            sep: Delimiter (default: ',')
            header: Whether to write column names (default: True)
        """
        if df is None:
            df = pd.DataFrame()

        df.to_csv(filepath, **options)

    @WordDecorator(
        "( df:DataFrame filepath:str [options:WordOptions] -- )",
        "Write DataFrame to Excel file",
        "TO_EXCEL",
    )
    async def TO_EXCEL(self, df: pd.DataFrame, filepath: str, options: dict[str, Any]) -> None:
        """Write DataFrame to Excel file.

        Options:
            sheet_name: Sheet name (default: 'Sheet1')
            index: Whether to write row index (default: True)
        """
        if df is None:
            df = pd.DataFrame()

        df.to_excel(filepath, **options)

    @WordDecorator(
        "( df:DataFrame filepath:str [options:WordOptions] -- )",
        "Write DataFrame to JSON file",
        "TO_JSON",
    )
    async def TO_JSON(self, df: pd.DataFrame, filepath: str, options: dict[str, Any]) -> None:
        """Write DataFrame to JSON file.

        Options:
            orient: 'records', 'index', 'columns', etc. (default: 'columns')
            indent: JSON indentation for pretty printing
        """
        if df is None:
            df = pd.DataFrame()

        df.to_json(filepath, **options)

    # ==================
    # Transformation Operations
    # ==================

    @ForthicDirectWord("( df:DataFrame forthic:str -- df:DataFrame )", "Map Forthic over DataFrame elements", "DF.MAP")
    async def DF_MAP(self, interp) -> None:
        """Map Forthic code over all elements in DataFrame.

        The Forthic code receives each element value on the stack and should
        leave a transformed value on the stack.
        """
        forthic = interp.stack_pop()
        df = interp.stack_pop()

        if df is None or df.empty:
            interp.stack_push(pd.DataFrame())
            return

        string_location = interp.get_string_location()
        result = df.copy()

        for col in result.columns:
            new_values = []
            for value in result[col]:
                interp.stack_push(value)
                await interp.run(forthic, string_location)
                new_values.append(interp.stack_pop())
            result[col] = new_values

        interp.stack_push(result)

    @ForthicDirectWord(
        "( df:DataFrame forthic:str [options:WordOptions] -- df:DataFrame )",
        "Apply Forthic to rows or columns",
        "DF.APPLY",
    )
    async def DF_APPLY(self, interp) -> None:
        """Apply Forthic to rows or columns.

        Options:
            axis: 0 for columns (default), 1 for rows

        For axis=1 (rows), the Forthic code receives each row as a record.
        For axis=0 (columns), the Forthic code receives each column as a Series.
        """
        # Check for options
        options = {}
        if len(interp.get_stack()) > 0:
            top = interp.stack_peek()
            from ..word_options import WordOptions
            if isinstance(top, WordOptions):
                opts = interp.stack_pop()
                options = opts.to_dict()

        forthic = interp.stack_pop()
        df = interp.stack_pop()

        if df is None or df.empty:
            interp.stack_push(pd.DataFrame())
            return

        axis = options.get("axis", 1)
        string_location = interp.get_string_location()
        result = []

        if axis == 1:  # Apply to rows
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                interp.stack_push(row_dict)
                await interp.run(forthic, string_location)
                result.append(interp.stack_pop())
        else:  # Apply to columns
            for col in df.columns:
                series = df[col]
                interp.stack_push(series)
                await interp.run(forthic, string_location)
                result.append(interp.stack_pop())

        interp.stack_push(pd.Series(result))

    @WordDecorator(
        "( df:DataFrame func_name:str [options:WordOptions] -- df:DataFrame )",
        "Transform with function name",
        "DF.TRANSFORM",
    )
    async def DF_TRANSFORM(self, df: pd.DataFrame, func_name: str, options: dict[str, Any]) -> pd.DataFrame:
        """Transform DataFrame with function name.

        Options:
            axis: 0 for columns (default), 1 for rows
        """
        if df is None or df.empty:
            return pd.DataFrame()

        axis = options.get("axis", 0)
        return df.transform(func_name, axis=axis)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Reset DataFrame index",
        "DF.RESET-INDEX",
    )
    async def DF_RESET_INDEX(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Reset DataFrame index.

        Options:
            drop: Whether to drop the old index (default: False)
        """
        if df is None or df.empty:
            return pd.DataFrame()

        drop = options.get("drop", False)
        return df.reset_index(drop=drop)

    @WordDecorator(
        "( df:DataFrame column:str [options:WordOptions] -- df:DataFrame )",
        "Set column as index",
        "DF.SET-INDEX",
    )
    async def DF_SET_INDEX(self, df: pd.DataFrame, column: str, options: dict[str, Any]) -> pd.DataFrame:
        """Set column as index.

        Options:
            drop: Whether to drop the column (default: True)
        """
        if df is None or df.empty:
            return pd.DataFrame()

        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")

        drop = options.get("drop", True)
        return df.set_index(column, drop=drop)

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Transpose DataFrame",
        "DF.TRANSPOSE",
    )
    async def DF_TRANSPOSE(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Transpose DataFrame (swap rows and columns)."""
        if df is None or df.empty:
            return pd.DataFrame()

        return df.transpose()

    @WordDecorator(
        "( df:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Unpivot DataFrame from wide to long format",
        "DF.MELT",
    )
    async def DF_MELT(self, df: pd.DataFrame, options: dict[str, Any]) -> pd.DataFrame:
        """Unpivot DataFrame from wide to long format.

        Options:
            id_vars: Columns to use as identifier variables
            value_vars: Columns to unpivot
            var_name: Name for variable column (default: 'variable')
            value_name: Name for value column (default: 'value')
        """
        if df is None or df.empty:
            return pd.DataFrame()

        id_vars = options.get("id_vars")
        value_vars = options.get("value_vars")
        var_name = options.get("var_name", "variable")
        value_name = options.get("value_name", "value")

        return pd.melt(df, id_vars=id_vars, value_vars=value_vars,
                       var_name=var_name, value_name=value_name)

    @WordDecorator(
        "( df:DataFrame column:str -- df:DataFrame )",
        "Explode list-like values into separate rows",
        "DF.EXPLODE",
    )
    async def DF_EXPLODE(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Explode list-like values in column into separate rows."""
        if df is None or df.empty:
            return pd.DataFrame()

        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")

        return df.explode(column)

    @WordDecorator(
        "( df:DataFrame to_replace:any value:any [options:WordOptions] -- df:DataFrame )",
        "Replace values in DataFrame",
        "DF.REPLACE",
    )
    async def DF_REPLACE(self, df: pd.DataFrame, to_replace: Any, value: Any,
                        options: dict[str, Any]) -> pd.DataFrame:
        """Replace values in DataFrame.

        Args:
            to_replace: Value(s) to replace
            value: Replacement value(s)
        """
        if df is None or df.empty:
            return pd.DataFrame()

        return df.replace(to_replace, value)

    # ==================
    # Merge & Join Operations
    # ==================

    @WordDecorator(
        "( left:DataFrame right:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Merge two DataFrames",
        "DF.MERGE",
    )
    async def DF_MERGE(self, left: pd.DataFrame, right: pd.DataFrame,
                      options: dict[str, Any]) -> pd.DataFrame:
        """Merge two DataFrames.

        Options:
            how: 'inner' (default), 'left', 'right', 'outer'
            on: Column(s) to join on
            left_on: Left DataFrame column(s) to join on
            right_on: Right DataFrame column(s) to join on
            suffixes: Tuple of suffixes for overlapping columns (default: ('_x', '_y'))
        """
        if left is None:
            left = pd.DataFrame()
        if right is None:
            right = pd.DataFrame()

        return pd.merge(left, right, **options)

    @WordDecorator(
        "( left:DataFrame right:DataFrame [options:WordOptions] -- df:DataFrame )",
        "Join DataFrames on index",
        "DF.JOIN",
    )
    async def DF_JOIN(self, left: pd.DataFrame, right: pd.DataFrame,
                     options: dict[str, Any]) -> pd.DataFrame:
        """Join DataFrames on index.

        Options:
            how: 'left' (default), 'right', 'outer', 'inner'
            lsuffix: Suffix for left DataFrame overlapping columns
            rsuffix: Suffix for right DataFrame overlapping columns
        """
        if left is None:
            left = pd.DataFrame()
        if right is None:
            right = pd.DataFrame()

        return left.join(right, **options)

    @WordDecorator(
        "( dfs:list [options:WordOptions] -- df:DataFrame )",
        "Concatenate DataFrames",
        "DF.CONCAT",
    )
    async def DF_CONCAT(self, dfs: list, options: dict[str, Any]) -> pd.DataFrame:
        """Concatenate list of DataFrames.

        Options:
            axis: 0 for rows (default), 1 for columns
            ignore_index: Whether to ignore index (default: False)
            keys: Labels for MultiIndex
        """
        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, **options)

    # ==================
    # String Operations
    # ==================

    @WordDecorator("( series:Series -- series:Series )", "Convert strings to uppercase", "STR.UPPER")
    async def STR_UPPER(self, series: pd.Series) -> pd.Series:
        """Convert strings in Series to uppercase."""
        if series is None or series.empty:
            return pd.Series()

        return series.str.upper()

    @WordDecorator("( series:Series -- series:Series )", "Convert strings to lowercase", "STR.LOWER")
    async def STR_LOWER(self, series: pd.Series) -> pd.Series:
        """Convert strings in Series to lowercase."""
        if series is None or series.empty:
            return pd.Series()

        return series.str.lower()

    @WordDecorator("( series:Series -- series:Series )", "Strip whitespace from strings", "STR.STRIP")
    async def STR_STRIP(self, series: pd.Series) -> pd.Series:
        """Strip leading and trailing whitespace from strings."""
        if series is None or series.empty:
            return pd.Series()

        return series.str.strip()

    @WordDecorator(
        "( series:Series pattern:str [options:WordOptions] -- series:Series )",
        "Check if strings contain pattern",
        "STR.CONTAINS",
    )
    async def STR_CONTAINS(self, series: pd.Series, pattern: str, options: dict[str, Any]) -> pd.Series:
        """Check if strings contain pattern (supports regex).

        Options:
            case: Whether to be case sensitive (default: True)
            regex: Whether pattern is regex (default: True)
        """
        if series is None or series.empty:
            return pd.Series()

        case = options.get("case", True)
        regex = options.get("regex", True)

        return series.str.contains(pattern, case=case, regex=regex, na=False)

    @WordDecorator(
        "( series:Series sep:str [options:WordOptions] -- series:Series )",
        "Split strings by separator",
        "STR.SPLIT",
    )
    async def STR_SPLIT(self, series: pd.Series, sep: str, options: dict[str, Any]) -> pd.Series:
        """Split strings by separator.

        Options:
            expand: Whether to expand into separate columns (default: False)
        """
        if series is None or series.empty:
            return pd.Series()

        expand = options.get("expand", False)
        return series.str.split(sep, expand=expand)

    @WordDecorator(
        "( series:Series pat:str repl:str [options:WordOptions] -- series:Series )",
        "Replace substring in strings",
        "STR.REPLACE",
    )
    async def STR_REPLACE(self, series: pd.Series, pat: str, repl: str,
                         options: dict[str, Any]) -> pd.Series:
        """Replace substring in strings.

        Options:
            regex: Whether pattern is regex (default: True)
        """
        if series is None or series.empty:
            return pd.Series()

        regex = options.get("regex", True)
        return series.str.replace(pat, repl, regex=regex)

    @WordDecorator(
        "( series:Series pattern:str [options:WordOptions] -- df:DataFrame )",
        "Extract regex pattern from strings",
        "STR.EXTRACT",
    )
    async def STR_EXTRACT(self, series: pd.Series, pattern: str, options: dict[str, Any]) -> pd.DataFrame:
        """Extract regex pattern from strings into DataFrame.

        The pattern should have capture groups which become columns.

        Options:
            expand: Whether to expand into DataFrame (default: True)
        """
        if series is None or series.empty:
            return pd.DataFrame()

        expand = options.get("expand", True)
        return series.str.extract(pattern, expand=expand)
