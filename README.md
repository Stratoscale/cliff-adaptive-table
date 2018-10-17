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
- **grep=pattern**: Print only rows where the pattern (regular expression) matches any of the values. Note that the values are searched recursively. Examples:
  - grep=name - Only print rows where one of the values matches 'name'.
  - grep=name|nombre - Only print rows where one of the values matches either 'name' or 'nombre'.
  - grep=name grep=nombre - Only print rows that have a value that matches 'name' _and_ a value that matches 'nombre'.
- **grep-i=pattern**: Same as _grep_, but matching is case-insensitive.
- **grep-v=pattern**: Skip rows that have a value that matches pattern. Examples:
  - grep-v=name - Only print rows where none of the values matches 'name'.
  - grep-v=name|nombre - Only print rows where none of the values matches either 'name' or 'nombre'.
  - grep-v=name grep-v=nombre - Print all rows _except_ rows that have a value that matches 'name' _and_ a value that matches 'nombre'.
- **grep-iv=pattern**, **grep-vi=pattern** - same as _grep-v_, but matching is case-insensitive.
- **head=_n_** - Only print first _n_ rows.
- **tail=_n_** - Only print last _n_ rows. Note that _tail_ is processed after _head_ regardless of their order in the command. Thus, if the entire table had 20 rows, _head=10_ _tail=5_ means that rows 6-10 are printed (where row number starts at 1).
- **columns=pattern** - Only print columns whose name match _pattern_ (matching is case-insensitive). If repeated, all columns matching any of the patterns will be printed. Thus, _columns=id|name_ is the same as _columns=id_ _columns=name_ (in contradistiction to _grep*_). Note that the _columns_ modifier is processed after the _grep*_ modifiers, so the matched values might not be printed.
- **columns-v=pattern** - Do not print columns whose name match _pattern_ (matching is case-insensitive). If repeated, all columns matching any of the patterns will be ignored. Thus, _columns-v=id|name_ is the same as _columns-v=id_ _columns-v=name_ (in contradistiction to _grep*_). Note that the _columns-v_ modifier is processed after the _grep*_ modifiers, so the matched values might not be printed.

These modifiers are processed in the following order: _grep*_, _head_, _tail_ and finally _columns_ and _columns-v_.

## Display Modifiers
Valid boolean values are `true`, `t`, `yes`, `y`, `false`, `f`, `no`, and `n` (case-insensitive).
- **color=bool** - Allow some columns to be colored according to the value (note: this only applies to the top level values, not to values in sub-tables). Default: true.
- **split-table=bool** - Allow table to be split to multiple tables that each have some of the columns. Default: false.
- **column-order=csv** - A comma-separated list of column names. Columns are sorted first by this list and then alphabetically. Default: `name,id,status,state`.
- **force-frames=bool** - Force frames around all sub-objects. Default: false.
- **horizontal-lines=bool** - Force horizontal lines between each row. Horizontal lines are normally only drawn if either the row above or below is split into multiple lines. Default: false.
- **split-words=**_always|except-ids|standard|never_. Default: _except-ids_.
  - `standard` - Cell values are split between words, and only words longer than the cell width are split.
  - `except-ids` - Same as _standard_ except that UUIDs and IPv4 addresses are never split.
  - `always` - Split cell values disregarding word limits. Might result in slightly shorter tables.
  - `never` - Turns off splitting of cell values, so the table looks like the _table_ formatter.
- **width=_n_** - Force a specific terminal width of _n_ characters instead of using the auto-detected value. Default: auto-detected value.
