from cliff.formatters.base import ListFormatter, SingleFormatter

from adaptive_table import AdaptiveTable
from filter_data import FilterData


class AdaptiveTableFormatter(ListFormatter, SingleFormatter):
    COLOR_GOOD = '\033[32m'  # green
    COLOR_BAD = '\033[31m'  # red
    COLOR_ACTIVE = '\033[33;1m'  # yellow
    COLOR_NEUTRAL = '\033[35m'  # magenta
    OUTPUT_COLUMN_COLORS = {
        'status': {
            'active': COLOR_GOOD,
            'ready': COLOR_GOOD,
            'error': COLOR_BAD,
            'migrating': COLOR_NEUTRAL,
            # for autoscaling groups
            'deleting': COLOR_ACTIVE,
            # for hot-upgrade
            'Preparing': COLOR_NEUTRAL,
            'Pending': COLOR_NEUTRAL,
            'Ready to Install': COLOR_NEUTRAL,
            'Installing': COLOR_ACTIVE,
            'Done': COLOR_GOOD,
        },
        'state': {  # for nodes
            'active': COLOR_GOOD,
            'down': COLOR_BAD,
            'up': COLOR_GOOD,
            'in_progress': COLOR_NEUTRAL,
            'in_maintenance': COLOR_NEUTRAL,
        }
    }

    def add_argument_group(self, parser):
        group = parser.add_argument_group('adaptive table formatter')
        group.add_argument('-m', '--modifiers', metavar='NAME=VALUE', nargs='*',
                           help='Modifiers. See https://www.stratoscale.com/docs/adaptive-table-output-format-modifiers/ for details.')

    def _emit(self, data, stdout, parsed_args):
        adaptive_table = AdaptiveTable(color_dict=self.OUTPUT_COLUMN_COLORS)
        filter_data = FilterData()
        non_table_modifiers = adaptive_table.parse_modifiers(parsed_args.modifiers)
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
