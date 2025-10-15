# core Module

[← Back to Index](../index.md)

Essential interpreter operations for stack manipulation, variables, control flow, and module system.

**25 words**

## Categories

- **Stack**: POP, DUP, SWAP
- **Variables**: VARIABLES, !, @, !@
- **Module**: EXPORT, USE_MODULES
- **Execution**: INTERPRET
- **Control**: IDENTITY, NOP, DEFAULT, *DEFAULT, NULL, ARRAY?
- **Options**: ~> (converts array to WordOptions)
- **Profiling**: PROFILE-START, PROFILE-TIMESTAMP, PROFILE-END, PROFILE-DATA
- **String**: INTERPOLATE, PRINT
- **Debug**: PEEK!, STACK!

## Options

INTERPOLATE and PRINT support options via the ~> operator using syntax: [.option_name value ...] ~> WORD
- separator: String to use when joining array values (default: ", ")
- null_text: Text to display for null/None values (default: "null")
- json: Use JSON formatting for all values (default: false)

## Examples

```forthic
5 .count ! "Count: .count" PRINT
"Items: .items" [.separator " | "] ~> PRINT
[1 2 3] PRINT                           # Direct printing: 1, 2, 3
[1 2 3] [.separator " | "] ~> PRINT    # With options: 1 | 2 | 3
{"name" "Alice"} [.json TRUE] ~> PRINT  # JSON format: {"name":"Alice"}
"Hello .name" INTERPOLATE .greeting !
[1 2 3] DUP SWAP
```

## Words

### !

**Stack Effect:** `( value:any variable:any -- )`

Sets variable value (auto-creates if string name)

---

### !@

**Stack Effect:** `( value:any variable:any -- value:any )`

Sets variable and returns value

---

### *DEFAULT

**Stack Effect:** `( value:any default_forthic:str -- result:any )`

Returns value or executes Forthic if value is None/empty string

---

### @

**Stack Effect:** `( variable:any -- value:any )`

Gets variable value (auto-creates if string name)

---

### ARRAY?

**Stack Effect:** `( value:any -- boolean:bool )`

Returns true if value is an array

---

### DEFAULT

**Stack Effect:** `( value:any default_value:any -- result:any )`

Returns value or default if value is None/empty string

---

### DUP

**Stack Effect:** `( a:any -- a:any a:any )`

Duplicates top stack item

---

### EXPORT

**Stack Effect:** `( names:list -- )`

Exports words from current module

---

### IDENTITY

**Stack Effect:** `( -- )`

Does nothing (identity operation)

---

### INTERPOLATE

**Stack Effect:** `( string:str [options:WordOptions] -- result:str )`

Interpolate variables (.name) and return result string. Use \. to escape literal dots.

---

### INTERPRET

**Stack Effect:** `( string:str -- )`

Interprets Forthic string in current context

---

### NOP

**Stack Effect:** `( -- )`

Does nothing (no operation)

---

### NULL

**Stack Effect:** `( -- null:None )`

Pushes None onto stack

---

### PEEK!

**Stack Effect:** `( -- )`

Prints top of stack and stops execution

---

### POP

**Stack Effect:** `( a:any -- )`

Removes top item from stack

---

### PRINT

**Stack Effect:** `( value:any [options:WordOptions] -- )`

Print value to stdout. Strings interpolate variables (.name). Use \. to escape literal dots.

---

### PROFILE-DATA

**Stack Effect:** `( -- profile_data:dict )`

Returns profiling data (word counts and timestamps)

---

### PROFILE-END

**Stack Effect:** `( -- )`

Stops profiling word execution

---

### PROFILE-START

**Stack Effect:** `( -- )`

Starts profiling word execution

---

### PROFILE-TIMESTAMP

**Stack Effect:** `( label:str -- )`

Records profiling timestamp with label

---

### STACK!

**Stack Effect:** `( -- )`

Prints entire stack (reversed) and stops execution

---

### SWAP

**Stack Effect:** `( a:any b:any -- b:any a:any )`

Swaps top two stack items

---

### USE_MODULES

**Stack Effect:** `( names:list -- )`

Imports modules by name

---

### VARIABLES

**Stack Effect:** `( varnames:list -- )`

Creates variables in current module

---

### ~>

**Stack Effect:** `( array:list -- options:WordOptions )`

Convert options array to WordOptions. Format: [.key1 val1 .key2 val2]

---


[← Back to Index](../index.md)
