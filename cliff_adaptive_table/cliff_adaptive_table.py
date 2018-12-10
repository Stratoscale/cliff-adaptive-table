from cliff.formatters.base import ListFormatter, SingleFormatter

from adaptive_table import AdaptiveTable
from filter_data import FilterData


class AdaptiveTableFormatter(ListFormatter, SingleFormatter):
    # OUTPUT_COLUMN_COLORS is a dictionary whose keys are column names
    # and whose values determine coloring for values.  for example,
    # {'status': {'success': '\033[32;1m',
    #             'failure': '\033[31;1m'}}
    # will color 'success' values in 'status' fields in bright green
    # and 'failure' values in bright red
    OUTPUT_COLUMN_COLORS = {}

    def add_argument_group(self, parser):
        group = parser.add_argument_group('adaptive table formatter')
        group.add_argument('-m', '--modifiers', metavar='NAME=VALUE', nargs='*', action='append',
                           help='Modifiers. Run table modifier list command or see https://www.stratoscale.com/docs/adaptive-table-output-format-modifiers/ for details.')

    def _emit(self, data, stdout, parsed_args):
        adaptive_table = AdaptiveTable(color_dict=self.OUTPUT_COLUMN_COLORS)
        filter_data = FilterData()
        modifiers = []
        for modifier_list in (parsed_args.modifiers or []):
            modifiers.extend(modifier_list)
        non_table_modifiers = adaptive_table.parse_modifiers(modifiers)
        invalid_modifiers = filter_data.parse_modifiers(non_table_modifiers)
        if invalid_modifiers:
            stdout.write('invalid modifiers: %s\n' % (' '.join(invalid_modifiers)))
            stdout.write('valid modifiers: %s\n' % (' '.join(adaptive_table.get_modifier_names() + filter_data.get_modifier_names())))
        data = filter_data.filter_data(data)
        stdout.write(adaptive_table.format(data))
        stdout.write('\n')

    def emit_list(self, column_names, data, stdout, parsed_args):
        combined = [dict(zip(column_names, row)) for row in data]
        self._emit(combined, stdout, parsed_args)

    def emit_one(self, column_names, data, stdout, parsed_args):
        combined = dict(zip(column_names, list(data)))
        self._emit(combined, stdout, parsed_args)
