# cliff-adaptive-table

This package installs a new formatter for [cliff](https://github.com/Stratoscale/cliff), which has the following improvements:
- sensitive to the terminal width
- supports hierarchical data structures
- supports filtering rows (grep) as well as columns
- highly configurable

## Installation
```bash
skipper make
pip install dist/cliff-adaptive-table-*.tar.gz
```

## Usage
```
symp> command [argument [argument...]] [--flag] --format adaptive_table [-m modifier [modifier...]]
```

## Filter Modifiers
All modifiers are of the form name=value. Supported modifiers are:
- **grep=pattern**: print only rows where the pattern (regular expression) matches any of the values. Note that the values are searched recursively. Examples:
  - grep=name - only print rows where one of the values matches 'name'
  - grep=name|nombre - only print rows where one of the values matches either 'name' or 'nombre'
  - grep=name grep=nombre - only print rows that have a value that matches 'name' _and_ a value that matches 'nombre'
- **grep-i=pattern**: same as _grep_, but matching is case-insensitive
- **grep-v=pattern**: skip rows that have a value that matches pattern. Examples:
  - grep-v=name - only print rows where none of the values matches 'name'
  - grep-v=name|nombre - only print rows where none of the values matches either 'name' or 'nombre'
  - grep-v=name grep-v=nombre - print all rows _except_ rows that have a value that matches 'name' _and_ a value that matches 'nombre'
- **grep-iv=pattern**, **grep-vi=pattern** - same as _grep-v_, but matching is case-insensitive
- **head=int** - only print first _n_ rows
- **tail=int** - only print last _n_ rows. Note that _tail_ is processed after _head_, so head=10 tail=5 means that rows 6-10 are printed (where row number starts at 1)
- **columns=pattern** - only print columns that match _pattern_. If repeated, all columns matching any of the pattern will be printed. Note that the _columns_ modifier is processed after the _grep*_ modifiers, so the matched values might not be printed.

## Display Modifiers
Valid boolean values are true, t, yes, y, false, f, no, and n (case-insensitive)
- **column-order=csv** - a comma-seperated list of column names. Columns are sorted first by this list and the alphabetically. Default: name,id
- **force-frames=bool** - force frames around all sub-objects
- **horizontal-lines=bool** - force horizontal lines between each row
- **split-words** - any of always, when-neccessary, or never:
  - when-necessary - cell values are split between words, and only words longer than the cell width are split
  - except-ids - same as _when-necessary_ except that UUIDs are never split. This is the default
  - always - split cell values disregarding word limits. Might result in slightly shorter tables
  - never - turns off splitting of cell values, so the table looks like the _table_ formatter
- **terminal-size=int** - force a terminal size instead of using the auto-detected value
- **max-str-length=int** - maximum string length to split cell values to. If the table does not fit in the terminal, cliff-adaptive-table performs binary search on the optimal number of characters to split column values. This modifiers determines the limit of the binary search. Default: 100
