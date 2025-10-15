# datetime Module

[← Back to Index](../index.md)

Date and time operations using Python's datetime with timezone support.

**15 words**

## Categories

- **Current**: TODAY, NOW
- **Time adjustment**: AM, PM
- **Conversion to**: >TIME, >DATE, >DATETIME, AT
- **Conversion from**: TIME>STR, DATE>STR, DATE>INT
- **Timestamps**: >TIMESTAMP, TIMESTAMP>DATETIME
- **Date math**: ADD-DAYS, SUBTRACT-DATES

## Examples

```forthic
TODAY
NOW
"14:30" >TIME
"2024-01-15" >DATE
TODAY "14:30" >TIME AT
TODAY 7 ADD-DAYS
```

## Words

### >DATE

**Stack Effect:** `( item -- date )`

Convert string or datetime to date

---

### >DATETIME

**Stack Effect:** `( str_or_timestamp -- datetime )`

Convert string or timestamp to datetime

---

### >TIME

**Stack Effect:** `( item -- time )`

Convert string or datetime to time

---

### >TIMESTAMP

**Stack Effect:** `( datetime -- timestamp )`

Convert datetime to Unix timestamp (seconds)

---

### ADD-DAYS

**Stack Effect:** `( date num_days -- date )`

Add days to a date

---

### AM

**Stack Effect:** `( time -- time )`

Convert time to AM (subtract 12 from hour if >= 12)

---

### AT

**Stack Effect:** `( date time -- datetime )`

Combine date and time into datetime

---

### DATE>INT

**Stack Effect:** `( date -- int )`

Convert date to integer (YYYYMMDD)

---

### DATE>STR

**Stack Effect:** `( date -- str )`

Convert date to YYYY-MM-DD string

---

### NOW

**Stack Effect:** `( -- datetime )`

Get current datetime

---

### PM

**Stack Effect:** `( time -- time )`

Convert time to PM (add 12 to hour if < 12)

---

### SUBTRACT-DATES

**Stack Effect:** `( date1 date2 -- num_days )`

Get difference in days between dates (date1 - date2)

---

### TIME>STR

**Stack Effect:** `( time -- str )`

Convert time to HH:MM string

---

### TIMESTAMP>DATETIME

**Stack Effect:** `( timestamp -- datetime )`

Convert Unix timestamp (seconds) to datetime

---

### TODAY

**Stack Effect:** `( -- date )`

Get current date

---


[← Back to Index](../index.md)
