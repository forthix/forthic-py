# pandas Module

[← Back to Index](../index.md)

Pandas DataFrame and Series operations for data manipulation and analysis.

**77 words**

## Categories

- **Conversion**: >DF, DF>, >SERIES, SERIES>
- **Inspection**: DF.INFO, DF.HEAD, DF.TAIL, DF.SHAPE, DF.COLUMNS, DF.DTYPES, DF.DESCRIBE, DF.NUNIQUE

## Options

Several words support options via the ~> operator using syntax: [.option_name value ...] ~> WORD
- index: Series/DataFrame index (list)
- name: Series name (str)
- n: Number of rows (int)

## Examples

```forthic
# Create DataFrame from records
[
[['name' 'Alice'] ['age' 30]] REC
[['name' 'Bob'] ['age' 25]] REC
] >DF
# Inspect data
DF.HEAD DF.INFO
# Convert back to records
DF>
```

## Words

### <DF!

**Stack Effect:** `( df:DataFrame series:Series column:str -- df:DataFrame )`

Set or add column to DataFrame

---

### >DF

**Stack Effect:** `( records:list -- df:DataFrame )`

Convert list of records to DataFrame

---

### >SERIES

**Stack Effect:** `( values:list [options:WordOptions] -- series:Series )`

Convert list to Series with optional index and name

---

### DF.AGG

**Stack Effect:** `( df_or_grouped:any agg_spec:any -- df:DataFrame )`

Aggregate using function name or dict

---

### DF.APPEND-ROW

**Stack Effect:** `( df:DataFrame row:dict -- df:DataFrame )`

Append single row to DataFrame

---

### DF.APPLY

**Stack Effect:** `( df:DataFrame forthic:str [options:WordOptions] -- df:DataFrame )`

Apply Forthic to rows or columns

---

### DF.APPLY-COL

**Stack Effect:** `( df:DataFrame column:str forthic:str -- series:Series )`

Apply Forthic to column

---

### DF.ASTYPE

**Stack Effect:** `( df:DataFrame column:str dtype:str -- df:DataFrame )`

Convert column to specified dtype

---

### DF.COLUMNS

**Stack Effect:** `( df:DataFrame -- columns:list )`

Get list of column names

---

### DF.CONCAT

**Stack Effect:** `( dfs:list [options:WordOptions] -- df:DataFrame )`

Concatenate DataFrames

---

### DF.CORR

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Compute correlation matrix

---

### DF.COUNT

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- result:any )`

Count non-NA values with optional axis

---

### DF.COV

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Compute covariance matrix

---

### DF.CROSSTAB

**Stack Effect:** `( index:any columns:any [options:WordOptions] -- df:DataFrame )`

Compute cross-tabulation of two factors

---

### DF.CUMPROD

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Cumulative product

---

### DF.CUMSUM

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Cumulative sum

---

### DF.DESCRIBE

**Stack Effect:** `( df:DataFrame -- stats:DataFrame )`

Get summary statistics

---

### DF.DIFF

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

First discrete difference

---

### DF.DROP-COLS

**Stack Effect:** `( df:DataFrame columns:list -- df:DataFrame )`

Drop columns from DataFrame

---

### DF.DROP-ROWS

**Stack Effect:** `( df:DataFrame indices:list -- df:DataFrame )`

Drop rows by index

---

### DF.DROPNA

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Drop rows with NA values

---

### DF.DTYPES

**Stack Effect:** `( df:DataFrame -- dtypes:dict )`

Get column data types as dict {col: dtype}

---

### DF.DUPLICATED

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- result:any )`

Find duplicate rows

---

### DF.EXPLODE

**Stack Effect:** `( df:DataFrame column:str -- df:DataFrame )`

Explode list-like values into separate rows

---

### DF.FILLNA

**Stack Effect:** `( df:DataFrame value:any [options:WordOptions] -- df:DataFrame )`

Fill NA values with specified value

---

### DF.FILTER

**Stack Effect:** `( df:DataFrame forthic:str -- df:DataFrame )`

Filter rows with Forthic predicate

---

### DF.GROUP-BY

**Stack Effect:** `( df:DataFrame columns:any -- grouped:DataFrameGroupBy )`

Group DataFrame by column(s)

---

### DF.HEAD

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Get first n rows (default 5)

---

### DF.ILOC

**Stack Effect:** `( df:DataFrame index:int -- record:dict )`

Get row by position as record

---

### DF.INFO

**Stack Effect:** `( df:DataFrame -- df:DataFrame )`

Print DataFrame info to stdout, return df for chaining

---

### DF.ISIN

**Stack Effect:** `( df:DataFrame column:str values:list -- df:DataFrame )`

Filter rows where column value is in values list

---

### DF.JOIN

**Stack Effect:** `( left:DataFrame right:DataFrame [options:WordOptions] -- df:DataFrame )`

Join DataFrames on index

---

### DF.LOC

**Stack Effect:** `( df:DataFrame label:any -- record:dict )`

Get row by label as record

---

### DF.MAP

**Stack Effect:** `( df:DataFrame forthic:str -- df:DataFrame )`

Map Forthic over DataFrame elements

---

### DF.MEAN

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- result:any )`

Mean values with optional axis

---

### DF.MEDIAN

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- result:any )`

Median values with optional axis

---

### DF.MELT

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Unpivot DataFrame from wide to long format

---

### DF.MERGE

**Stack Effect:** `( left:DataFrame right:DataFrame [options:WordOptions] -- df:DataFrame )`

Merge two DataFrames

---

### DF.NLARGEST

**Stack Effect:** `( df:DataFrame column:str n:int -- df:DataFrame )`

Get top N rows by column values

---

### DF.NUNIQUE

**Stack Effect:** `( df:DataFrame -- counts:dict )`

Count unique values per column

---

### DF.PCT-CHANGE

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Percentage change between current and prior element

---

### DF.PIVOT

**Stack Effect:** `( df:DataFrame values:str index:str [options:WordOptions] -- df:DataFrame )`

Create pivot table

---

### DF.PIVOT-TABLE

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Create advanced pivot table with aggregation

---

### DF.QUERY

**Stack Effect:** `( df:DataFrame query_str:str -- df:DataFrame )`

Query DataFrame with pandas expression

---

### DF.RANK

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Rank values along axis

---

### DF.RENAME-COLS

**Stack Effect:** `( df:DataFrame mapping:dict -- df:DataFrame )`

Rename columns using dict mapping

---

### DF.REPLACE

**Stack Effect:** `( df:DataFrame to_replace:any value:any [options:WordOptions] -- df:DataFrame )`

Replace values in DataFrame

---

### DF.RESET-INDEX

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Reset DataFrame index

---

### DF.ROLLING

**Stack Effect:** `( df:DataFrame window:int [options:WordOptions] -- rolling:Rolling )`

Create rolling window object

---

### DF.SAMPLE

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Random sample of rows with optional parameters

---

### DF.SELECT-DTYPES

**Stack Effect:** `( df:DataFrame dtypes:any -- df:DataFrame )`

Select columns by data type(s)

---

### DF.SET-INDEX

**Stack Effect:** `( df:DataFrame column:str [options:WordOptions] -- df:DataFrame )`

Set column as index

---

### DF.SHAPE

**Stack Effect:** `( df:DataFrame -- shape:list )`

Get DataFrame shape as [rows, cols]

---

### DF.SORT

**Stack Effect:** `( df:DataFrame by:any [options:WordOptions] -- df:DataFrame )`

Sort DataFrame by column(s)

---

### DF.SORT-INDEX

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Sort DataFrame by index

---

### DF.SUM

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- result:any )`

Sum values with optional axis

---

### DF.TAIL

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Get last n rows (default 5)

---

### DF.TRANSFORM

**Stack Effect:** `( df:DataFrame func_name:str [options:WordOptions] -- df:DataFrame )`

Transform with function name

---

### DF.TRANSPOSE

**Stack Effect:** `( df:DataFrame [options:WordOptions] -- df:DataFrame )`

Transpose DataFrame

---

### DF.VALUE-COUNTS

**Stack Effect:** `( series:Series -- counts:Series )`

Count unique values in Series

---

### DF>

**Stack Effect:** `( df:DataFrame -- records:list )`

Convert DataFrame to list of records

---

### DF@

**Stack Effect:** `( df:DataFrame column:str -- series:Series )`

Get column by name

---

### DF@@

**Stack Effect:** `( df:DataFrame columns:list -- df:DataFrame )`

Get multiple columns as DataFrame

---

### READ_CSV

**Stack Effect:** `( filepath:str [options:WordOptions] -- df:DataFrame )`

Read CSV file into DataFrame

---

### READ_EXCEL

**Stack Effect:** `( filepath:str [options:WordOptions] -- df:DataFrame )`

Read Excel file into DataFrame

---

### READ_JSON

**Stack Effect:** `( filepath:str [options:WordOptions] -- df:DataFrame )`

Read JSON file into DataFrame

---

### SERIES>

**Stack Effect:** `( series:Series -- values:list )`

Convert Series to list of values

---

### STR.CONTAINS

**Stack Effect:** `( series:Series pattern:str [options:WordOptions] -- series:Series )`

Check if strings contain pattern

---

### STR.EXTRACT

**Stack Effect:** `( series:Series pattern:str [options:WordOptions] -- df:DataFrame )`

Extract regex pattern from strings

---

### STR.LOWER

**Stack Effect:** `( series:Series -- series:Series )`

Convert strings to lowercase

---

### STR.REPLACE

**Stack Effect:** `( series:Series pat:str repl:str [options:WordOptions] -- series:Series )`

Replace substring in strings

---

### STR.SPLIT

**Stack Effect:** `( series:Series sep:str [options:WordOptions] -- series:Series )`

Split strings by separator

---

### STR.STRIP

**Stack Effect:** `( series:Series -- series:Series )`

Strip whitespace from strings

---

### STR.UPPER

**Stack Effect:** `( series:Series -- series:Series )`

Convert strings to uppercase

---

### TO_CSV

**Stack Effect:** `( df:DataFrame filepath:str [options:WordOptions] -- )`

Write DataFrame to CSV file

---

### TO_EXCEL

**Stack Effect:** `( df:DataFrame filepath:str [options:WordOptions] -- )`

Write DataFrame to Excel file

---

### TO_JSON

**Stack Effect:** `( df:DataFrame filepath:str [options:WordOptions] -- )`

Write DataFrame to JSON file

---


[← Back to Index](../index.md)
