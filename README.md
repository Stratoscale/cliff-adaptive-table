# cliff-adaptive-table

This package installs a new formatter for [cliff](https://github.com/Stratoscale/cliff), which has the following improvements:
- sensitive to the terminal width
- supports hierarchical data structures
- supports filtering rows (grep) as well as columns
- highly configurable

## Installation
Install [skipper](https://github.com/Stratoscale/skipper) and then
```
skipper make
pip install dist/cliff-adaptive-table-*.tar.gz
```

## Modifiers

The modifiers are documented in `ADAPTIVE_TABLE_HELP` in
`cliff_adaptive_table/adaptive_table.py` and in `FILTER_DATA_HELP` in
`cliff_adaptive_table/filter_data.py`. The documentation can also be
printed by cliff adaptive table itself:

```
from cliff_adaptive_table import adaptive_table, filter_data

table = adaptive_table.AdaptiveTable()
help = {'Display Modifiers': table().help(),
        'Filter Modifiers': filter_data.FilterData().help()}
print table.format(help)
```


## Usage
To use in a cliff-based CLI, change the format to `adaptive_table`:
```
prompt> command [argument [argument...]] [--flag] --format adaptive_table [-m modifier [modifier...]]
```
Where `modifier` is in the format `name=value`.

To use in Python code:
```
from cliff_adaptive_table import adaptive_table, filter_data

modifiers = ['force-frames=y', 'columns=name|id']

table = adaptive_table.AdaptiveTable()
fd = filter_data.FilterData()
table.parse_modifiers(modifiers)
fd.parse_modifiers(modifiers)
data = fd.filter_data(data)

print table.format(data)
```