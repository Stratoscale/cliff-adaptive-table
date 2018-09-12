import re
from cliff.formatters.base import ListFormatter, SingleFormatter

from adaptive_table import AdaptiveTable
from modifier import parse_modifiers
from filter_data import filter_data


class AdaptiveTableFormatter(ListFormatter, SingleFormatter):
    MODIFIERS = {'grep': re.compile,
                 'grep-v': re.compile,
                 'grep-i': lambda pattern: re.compile(pattern, re.IGNORECASE),
                 'grep-iv': lambda pattern: re.compile(pattern, re.IGNORECASE),
                 'columns': lambda pattern: re.compile(pattern, re.IGNORECASE),
                 'head': int,
                 'tail': int}

    def add_argument_group(self, parser):
        group = parser.add_argument_group('adaptive table formatter')
        group.add_argument('-m', '--modifiers', nargs='*', help='modifiers')

    def _emit(self, data, stdout, parsed_args):
        adaptive_table = AdaptiveTable()
        non_table_modifiers = adaptive_table.parse_modifiers(parsed_args.modifiers)
        filter_modifiers, unrecognized_modifiers = parse_modifiers(self.MODIFIERS, non_table_modifiers)
        if unrecognized_modifiers:
            stdout.write('unrecognized modifiers: %s\n' % (', '.join(unrecognized_modifiers)))
        greps = [filter_modifiers.get('grep', None), filter_modifiers.get('grep-i', None)]
        reverse_greps = [filter_modifiers.get('grep-v', None), filter_modifiers.get('grep-vi', None), filter_modifiers.get('grep-iv', None)]
        data = filter_data(data,
                           [filter_modifiers['columns']] if 'columns' in filter_modifiers else None,
                           [pattern for pattern in greps if pattern],
                           [pattern for pattern in reverse_greps if pattern],
                           filter_modifiers.get('head'),
                           filter_modifiers.get('tail'))
        stdout.write(adaptive_table.format(data))
        stdout.write('\n')

    def emit_list(self, column_names, data, stdout, parsed_args):
        combined = [dict(zip(column_names, row)) for row in data]
        self._emit(combined, stdout, parsed_args)

    def emit_one(self, column_names, data, stdout, parsed_args):
        combined = dict(zip(column_names, list(data)))
        self._emit(combined, stdout, parsed_args)
