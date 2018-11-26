import re
import time
import uuid
import json
import fcntl
import struct
import termios
from string import hexdigits

from adaptive_table_def import AdaptiveTableDef
import modifier


class SplitWords(object):
    ALWAYS = 'always'
    EXCEPT_IDS = 'except-ids'
    STANDARD = 'standard'
    NEVER = 'never'


ADAPTIVE_TABLE_HELP = {
    'description': 'Valid Boolean values are true, t, yes, y, false, f, no, and n (case-insensitive).',
    'modifiers':
    [
        {
            'modifier': 'color=<bool>',
            'description': 'Determines whether to display colored outputs in color. (Note: If \'true\', it applies only to the values in top level tables, but not those in sub-tables.)',
            'default': 'true'
        },
        {
            'modifier': 'split-table=<bool>',
            'description': 'When output exceeds terminal width, determines whether to split it into multiple, terminal-width tables, each containing some of the columns.',
            'default': 'false'
            },
        {
            'modifier': 'column-order=<csv>',
            'description': 'Displays the columns according to a comma-separated list of column headers. The unlisted columns are displayed after the listed ones in alphabetical order.',
            'default': 'name,id,status,state'
        },
        {
            'modifier': 'force-frames=<bool>',
            'description': 'Determines whether to display frames around all sub-tables',
            'default': 'false'
        },
        {
            'modifier': 'horizontal-lines=<bool>',
            'description': 'Determines whether to display horizontal lines between each row of output. Horizontal lines are normally only drawn if either the row above or below is split into multiple lines.',
            'default': 'false'
        },
        {
            'modifier': 'split-words=<always|except-ids|standard|never>',
            'description': 'Determines whether to split words when displaying cell values that are longer than their cell width. There are four different policies: standard|except-ids|always|never.',
            'default': 'except-ids',
            'examples':
            [
                'standard - Cell values are split only between words. Words are not split unless a word is longer than the cell width.',
                'except-ids - Same as standard except that UUIDs and IPv4 addresses are never split.',
                'always - Cell values may be split both between words and within words. This may result in slightly shorter tables.',
                'never - Cell values are never split. This causes the table to look like the output of the regular table formatter.'
            ]
        },
        {
            'modifier': 'width=<n>',
            'description': 'Sets the width of the terminal to n characters instead of using the auto-detected value.',
            'default': 'auto-detected value'
        },
        {
            'modifier': 'transpose=<bool>',
            'description': 'Rotate the table diagonally, such that the rows are turned into columns and columns are turned into rows. Useful when there are few complex objects.',
            'default': 'false',
        }
    ]
}


class AdaptiveTable(object):
    _MODIFIERS = {'width': modifier.to_int,
                  'force-frames': modifier.boolean,
                  'horizontal-lines': modifier.boolean,
                  'split-words': modifier.to_str,
                  'column-order': modifier.csv,
                  'split-table': modifier.boolean,
                  'color': modifier.boolean,
                  'transpose': modifier.boolean}
    _DEFAULT_COLUMN_ORDER = ['id', 'name', 'status', 'state']
    _IP_PATTERN = re.compile('^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$')
    _TTL = 1.0  # maximum time to try to optimize the table

    def __init__(self,
                 color_dict=None,
                 color=True,
                 width=None,
                 split_table=None,
                 max_depth=None,
                 force_frames=False,
                 horizontal_lines=False,
                 split_words=SplitWords.EXCEPT_IDS,
                 column_order=_DEFAULT_COLUMN_ORDER,
                 transpose=False,
                 ttl=_TTL):
        self._color_dict = color_dict or {}
        self._color = color
        self._width = width or self._get_terminal_size()[1]
        self._split_table = split_table
        self._max_depth = max_depth
        self._force_frames = force_frames
        self._split_words = split_words
        self._horizontal_lines = horizontal_lines
        self._column_order = column_order or self._DEFAULT_COLUMN_ORDER
        self._transpose = transpose
        self._transposable = True
        self._set_key_sorter()
        if ttl is None:
            self._timeout = None
        else:
            self._timeout = time.time() + ttl

    def parse_modifiers(self, args):
        recognized, unrecognized = modifier.parse_modifiers(self._MODIFIERS, args)
        for key, value in recognized.iteritems():
            setattr(self, '_' + key.replace('-', '_'), value)
        self._set_key_sorter()
        return unrecognized

    def get_modifier_names(self):
        return self._MODIFIERS.keys()

    def _set_key_sorter(self):
        if self._column_order:
            column_value = {key.lower(): index - len(self._column_order) for index, key in enumerate(self._column_order)}
            self._key_sorter = lambda item: [column_value.get(unicode(item).lower(), 0), item]
        else:
            self._key_sorter = lambda item: item

    def _format_table(self, raw_headers, raw_data, all_colors, depth, compact):
        if not raw_data:
            return unicode(raw_data)

        transpose = (depth == 0 and self._transpose and self._transposable)

        if transpose:
            transposed = self._transpose_table(raw_headers, raw_data)
            headers = []
            vertical = True
        else:
            transposed = None
            headers = raw_headers
            vertical = not raw_headers
        header_width = max(len(header) for header in raw_headers) if raw_headers else 0

        all_data, all_widths = self._prepare_data_for_formatting(headers, transposed or raw_data)

        lines = []
        first_column = 0
        while raw_headers is None or first_column < len(all_data[0]):
            if depth == 0 and raw_headers and self._split_table:
                last_column = len(raw_headers) + 1
                last_column = len(all_data[0]) + 1
                while last_column > first_column:
                    if self._timeout and time.time() > self._timeout:
                        raise RuntimeError
                    widths = all_widths[first_column:last_column]
                    if transpose:
                        widths = [header_width] + widths
                    indent = 0 if first_column == 0 or transposed else 2
                    table_def = AdaptiveTableDef(widths, depth, compact, self._force_frames, self._horizontal_lines, indent, self._transpose, vertical, raw_headers[first_column:last_column])
                    if table_def.total_width() <= self._width or first_column + 1 == last_column:
                        if transpose:
                            data = [[[raw_headers[index]]] + one_row[first_column:last_column] for index, one_row in enumerate(all_data)]
                        else:
                            data = [one_row[first_column:last_column] for one_row in all_data]
                        if all_colors:
                            if transpose:
                                colors = [[None] + one_row[first_column:last_column] for one_row in all_colors]
                            else:
                                colors = [one_row[first_column:last_column] for one_row in all_colors]
                        else:
                            colors = None
                        first_column = last_column
                        break
                    last_column -= 1
            else:
                if depth == 0 and all_colors:
                    if transpose:
                        colors = [[None] + row for row in all_colors]
                    else:
                        colors = all_colors
                else:
                    colors = None
                if transpose:
                    data = [[[raw_headers[index]]] + one_row for index, one_row in enumerate(all_data)]
                    widths = [header_width] + all_widths
                else:
                    data = all_data
                    widths = all_widths
                table_def = AdaptiveTableDef(widths, depth, compact, self._force_frames, self._horizontal_lines, 0, self._transpose, vertical, raw_headers)

            if lines and transpose:
                lines.append('')
            self._format_columns(table_def, widths, colors, depth, data, lines)
            if not raw_headers or depth > 0 or not self._split_table:
                break
        return '\n'.join(lines)

    def _prepare_data_for_formatting(self, headers, raw_data):
        all_widths = [0] * max(len(datum) for datum in raw_data)
        all_data = []
        if headers:
            raw_data = [headers] + raw_data
        for raw_row in raw_data:
            row = [unicode(item).split('\n') for item in raw_row]
            for index, item in enumerate(row):
                all_widths[index] = max(all_widths[index], max(len(line) for line in item))
            all_data.append(row)
        return all_data, all_widths

    def _format_columns(self, table_def, widths, colors, depth, data, lines):
        def _add_color_keep_width(string, color_prefix, width):
            if not color_prefix:
                return string
            else:
                return ''.join((color_prefix, string, '\033[0m', ' ' * (width - len(string))))

        def _add_color_to_row(row_index, colors, widths, row):
            if not colors or not colors[row_index]:
                return row
            row_colors = colors[row_index]
            color_row = []
            for column_index, value in enumerate(row):
                if column_index < len(row_colors):
                    value = [_add_color_keep_width(item, row_colors[column_index], widths[column_index]) for item in value]
                color_row.append(value)
            return color_row

        prev_max_lines = 0
        for row_index, row in enumerate(data):
            max_lines = max(len(item) for item in row)
            sep = table_def.get_separator(row_index, max_lines, prev_max_lines)
            if sep:
                lines.append(sep)
            for index in xrange(max_lines):
                row = _add_color_to_row(row_index, colors, widths, row)
                row = row + [''] * (len(widths) - len(row))
                lines.append(table_def.line_format % tuple(self._get_line(item, index) for item in row))
            prev_max_lines = max_lines
        if depth == 0 or self._force_frames:
            lines.append(table_def.get_end_separator())

    def _get_line(self, lines, index):
        return lines[index] if index < len(lines) else ''

    def _split_string(self, string, max_str_length):
        def _simple_split(string, max_str_length):
            return [string[0 + i:max_str_length + i] for i in range(0, len(string), max_str_length)]

        def _append_word(line, word):
            if line:
                line += ' '
            line += word
            return line

        def _should_not_be_split(value):
            if len(value) in (32, 64) and not value.lstrip(hexdigits):
                return True
            if len(value) in (32, 36):
                try:
                    uuid.UUID(value)
                    return True
                except:
                    pass
            return bool(self._IP_PATTERN.match(value))

        string = unicode(string)
        if not max_str_length or self._split_words == SplitWords.NEVER:
            return string
        if self._split_words == SplitWords.ALWAYS:
            return '\n'.join(_simple_split(string, max_str_length))
        if self._split_words == SplitWords.EXCEPT_IDS and _should_not_be_split(string):
            return string
        lines = []
        current_line = ''
        for word in string.split():
            if len(_append_word(current_line, word)) <= max_str_length:
                current_line = _append_word(current_line, word)
            else:
                if len(word) <= max_str_length:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    if self._split_words in (SplitWords.EXCEPT_IDS, SplitWords.STANDARD):
                        space_left = max(0, max_str_length - len(current_line) - (1 if current_line else 0))
                        if space_left:
                            lines.append(_append_word(current_line, word[:space_left]))
                        else:
                            if current_line:
                                lines.append(current_line)
                        sub_lines = _simple_split(word[space_left:], max_str_length)
                        lines.extend(sub_lines[:-1])
                        current_line = sub_lines[-1]
                    else:
                        lines.append(word)
                        current_line = ''

        if current_line:
            lines.append(current_line)
        return '\n'.join(lines)

    def _get_keys_of_a_list_of_dicts(self, data):
        keys = set()
        for item in data:
            if isinstance(item, dict):
                keys.update(item.iterkeys())
        return sorted(keys, key=self._key_sorter)

    def _format_cell(self, data, depth, compact, max_str_length):
        if self._timeout and time.time() > self._timeout:
            raise RuntimeError
        if isinstance(data, (str, unicode)):
            return self._split_string(data, max_str_length)
        if self._max_depth is not None and depth >= self._max_depth:
            return json.dumps(data, sort_keys=True)
        if isinstance(data, dict):
            if not data:
                return {}
            keys = sorted(data.iterkeys(), key=self._key_sorter)
            table = [[self._split_string(key, max_str_length),
                      self._format_cell(data[key], depth + 1, compact, max_str_length)] for key in keys]
            return self._format_table(None, table, None, depth, compact)

        if isinstance(data, (list, tuple)):
            table = []
            headers = []
            keys = self._get_keys_of_a_list_of_dicts(data)
            headers = [self._split_string(key, max_str_length) for key in keys]
            for item in data:
                if isinstance(item, dict):
                    table.append([self._format_cell(item.get(key, ''), depth + 1, compact, max_str_length) for key in keys])
            formatted = self._format_table(headers, table, None, depth, compact)
            non_dicts = [self._format_cell(item, depth + 1, compact, max_str_length) for item in data if not isinstance(item, dict)]
            if non_dicts:
                non_dicts_table = [[self._format_cell(value, depth + 1, compact, max_str_length)] for value in non_dicts]
                return self._format_table(None, non_dicts_table, None, depth, compact)
            return formatted
        if data is True:
            return 'true'
        elif data is False:
            return 'false'
        else:
            return unicode(data)

    def _format(self, data, colors, compact, max_str_length):
        if isinstance(data, dict):
            keys = sorted(data.iterkeys(), key=self._key_sorter)
            table = [[key, self._format_cell(data[key], 1, compact, max_str_length)] for key in keys]
            return self._format_table(None, table, colors, 0, compact)

        if isinstance(data, (list, tuple)):
            table = []
            headers = []
            keys = self._get_keys_of_a_list_of_dicts(data)
            headers = [self._split_string(key, max_str_length) for key in keys]
            for item in data:
                if isinstance(item, dict):
                    table.append([self._format_cell(item.get(key, ''), 1, compact, max_str_length) for key in keys])
            formatted = self._format_table(headers, table, colors, 0, compact)
            non_dicts = [self._format_cell(item, 1, compact, max_str_length) for item in data if not isinstance(item, dict)]
            if non_dicts:
                formatted += '\n' + self._format_table(None, non_dicts, colors, 0, compact)
            return formatted

        return self._format_cell(data, 1, compact, max_str_length)

    def _get_item_color(self, key, value):
        if isinstance(key, (str, unicode)) and isinstance(value, (str, unicode)):
            return self._color_dict.get(key, {}).get(value)
        return None

    def _get_data_colors(self, data):
        def _get_dict_colors(keys, data):
            if isinstance(data, dict):
                return [self._get_item_color(key, data.get(key)) for key in keys]
            return None

        if not self._color:
            return None
        if isinstance(data, dict):
            return [[None, color] for color in _get_dict_colors(sorted(data.iterkeys(), key=self._key_sorter), data)]
        if isinstance(data, (list, tuple)):
            keys = self._get_keys_of_a_list_of_dicts(data)
            return [[]] + [_get_dict_colors(keys, item) for item in data]
        return None

    def _adaptive_format(self, data, colors):
        def table_fits(table, width):
            table_width = table.find('\n')
            if table_width < 0:
                table_width = len(table)
            return table_width <= width
        # first try table without splitting strings
        table = self._format(data, colors, compact=False, max_str_length=None)
        if table_fits(table, self._width):
            return table
        lower_limit = 10
        upper_limit = 100
        # find upper limit to string length
        while True:
            table = self._format(data, colors, compact=False, max_str_length=upper_limit)
            if table_fits(table, self._width):
                lower_limit = upper_limit
                upper_limit *= 2
            else:
                break
        # find maximum string length with which the table still fits
        max_str_length = (lower_limit + upper_limit) / 2
        while lower_limit < max_str_length:
            max_str_length = (lower_limit + upper_limit) / 2
            table = self._format(data, colors, compact=True, max_str_length=max_str_length)
            if table_fits(table, self._width):
                lower_limit = max_str_length
            else:
                upper_limit = max_str_length
        # try non-compact table, it often fits
        non_compact_table = self._format(data, colors, compact=False, max_str_length=max_str_length)
        if table_fits(non_compact_table, self._width):
            return non_compact_table
        if not table_fits(table, self._width):
            # give up, just make sure each row is printed in exactly one line
            self._max_depth = 1
            self._split_words = SplitWords.NEVER
            table = self._format(data, colors, compact=False, max_str_length=None)
        return table

    def _transpose_table(self, headers, data):
        transposed = []
        for index in xrange(len(data[0])):
            transposed.append([row[index] for row in data])
        return transposed

    def format(self, data):
        if isinstance(data, (list, tuple)) and len(data) == 1:
            data = data[0]
        self._transposable = isinstance(data, (list, tuple))
        colors = self._get_data_colors(data)
        orig_colors = colors
        if colors and self._transpose and self._transposable:
            colors = self._transpose_table([None] * len(colors[1]), colors[1:])
        try:
            return self._adaptive_format(data, colors)
        except:
            # timeout, just use the quickest table
            self._max_depth = 1
            self._split_words = SplitWords.NEVER
            self._split_table = False
            self._transpose = False
            self._timeout = None
            return self._format(data, orig_colors, compact=False, max_str_length=None)

    def _get_terminal_size(self):
        try:
            def ioctl_GWINSZ(fd):
                try:
                    return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
                except:
                    pass
            cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
            if cr is None:
                cr = (1000, 1000)
            return cr
        except:
            return 1000, 1000

    def help(self):
        return ADAPTIVE_TABLE_HELP
