from cliff.formatters.base import ListFormatter, SingleFormatter

from adaptive_table import AdaptiveTable
from filter_data import FilterData


class AdaptiveTableFormatter(ListFormatter, SingleFormatter):

    def add_argument_group(self, parser):
        group = parser.add_argument_group('adaptive table formatter')
        group.add_argument('-m', '--modifiers', nargs='*', help='modifiers')

    def _emit(self, data, stdout, parsed_args):
        adaptive_table = AdaptiveTable()
        filter_data = FilterData()
        non_table_modifiers = adaptive_table.parse_modifiers(parsed_args.modifiers)
        unrecognized_modifiers = filter_data.parse_modifiers(non_table_modifiers)
        if unrecognized_modifiers:
            stdout.write('unrecognized modifiers: %s\n' % (', '.join(unrecognized_modifiers)))
        data = filter_data.filter_data(data)
        stdout.write(adaptive_table.format(data))
        stdout.write('\n')

    def emit_list(self, column_names, data, stdout, parsed_args):
        combined = [dict(zip(column_names, row)) for row in data]
        self._emit(combined, stdout, parsed_args)

    def emit_one(self, column_names, data, stdout, parsed_args):
        combined = dict(zip(column_names, list(data)))
        self._emit(combined, stdout, parsed_args)
