import uuid
import yaml
import fcntl
import struct
import termios

from adaptive_table_def import AdaptiveTableDef
import modifier


class SplitWords(object):
    ALWAYS = 'always'
    EXCEPT_IDS = 'except-ids'
    WHEN_NECESSARY = 'when-neccessary'
    NEVER = 'never'


class AdaptiveTable(object):
    def __init__(self,
                 max_str_length=100,
                 terminal_size=None,
                 max_depth=None,
                 force_frames=False,
                 horizontal_lines=False,
                 split_words=SplitWords.EXCEPT_IDS,
                 column_order='name,id'):
        self._terminal_size = terminal_size
        self._max_str_length = max_str_length
        self._max_depth = max_depth
        self._force_frames = force_frames
        self._split_words = split_words
        self._horizontal_lines = horizontal_lines
        self._column_order = column_order or ['name', 'id']
        self._set_key_sorter()

    def parse_modifiers(self, args):
        MODIFIERS = {'terminal-size': modifier.to_int,
                     'force-frames': modifier.boolean,
                     'horizontal-lines': modifier.boolean,
                     'split-words': modifier.to_str,
                     'column-order': modifier.csv,
                     'max-str-length': modifier.to_int}
        recognized, unrecognized = modifier.parse_modifiers(MODIFIERS, args)
        for key, value in recognized.iteritems():
            setattr(self, '_' + key.replace('-', '_'), value)
        self._set_key_sorter()
        return unrecognized

    def _set_key_sorter(self):
        if self._column_order:
            self._column_order = {key.lower(): index - len(self._column_order) for index, key in enumerate(self._column_order)}
            self._key_sorter = lambda item: [self._column_order.get(str(item).lower(), 0), item]
        else:
            self._key_sorter = lambda item: item

    def _format_table(self, headers, raw_data, depth, compact):
        if not raw_data:
            return str(raw_data)
        widths = [0] * max(len(datum) for datum in raw_data)
        data = []
        if headers:
            raw_data = [headers] + raw_data
        for raw_row in raw_data:
            row = [str(item).split('\n') for item in raw_row]
            for index, item in enumerate(row):
                widths[index] = max(widths[index], max(len(line) for line in item))
            data.append(row)
        table_def = AdaptiveTableDef(widths, depth, compact, self._force_frames, self._horizontal_lines, headers)

        lines = []
        prev_max_lines = 0
        for row_index, row in enumerate(data):
            max_lines = max(len(item) for item in row)
            sep = table_def.get_separator(row_index, max_lines, prev_max_lines)
            if sep:
                lines.append(sep)
            for index in xrange(max_lines):
                row = row + [''] * (len(widths) - len(row))
                lines.append(table_def.line_format % tuple(self._get_line(item, index) for item in row))
            prev_max_lines = max_lines
        if depth == 0 or self._force_frames:
            lines.append(table_def.get_end_separator())
        return '\n'.join(lines)

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

        string = str(string)
        if not max_str_length:
            return string
        if self._split_words == SplitWords.ALWAYS:
            return '\n'.join(_simple_split(string, max_str_length))
        if self._split_words == SplitWords.EXCEPT_IDS:
            try:
                uuid.UUID(string)
                return string
            except:
                pass
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
                    if self._split_words in (SplitWords.EXCEPT_IDS, SplitWords.WHEN_NECESSARY):
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

    def _format_cell(self, data, depth, compact, max_str_length):
        if isinstance(data, (str, unicode)):
            return self._split_string(data, max_str_length)
        if self._max_depth is not None and depth >= self._max_depth:
            return yaml.dumps(data, indent=1 if compact else 2, sort_keys=True)
        if isinstance(data, dict):
            if not data:
                return {}
            table = [[self._split_string(key, max_str_length),
                      self._format_cell(value, depth + 1, compact, max_str_length)] for key, value in sorted(data.iteritems())]
            return self._format_table(None, table, depth, compact)

        if isinstance(data, (list, tuple)):
            table = []
            headers = []
            keys = set()
            for item in data:
                if isinstance(item, dict):
                    keys.update(item.iterkeys())
            keys = sorted(keys, key=self._key_sorter)
            headers = [self._split_string(key, max_str_length) for key in keys]
            for item in data:
                if isinstance(item, dict):
                    table.append([self._format_cell(item.get(key, ''), depth + 1, compact, max_str_length) for key in keys])
            formatted = self._format_table(headers, table, depth, compact)
            non_dicts = [self._format_cell(item, depth + 1, compact, max_str_length) for item in data if not isinstance(item, dict)]
            if non_dicts:
                non_dicts_table = [[self._format_cell(value, depth + 1, compact, max_str_length)] for value in non_dicts]
                return self._format_table(None, non_dicts_table, depth, compact)
            return formatted
        return str(data)

    def _format(self, data, compact, max_str_length):
        if isinstance(data, (list, tuple)) and len(data) == 1:
            data = data[0]
        if isinstance(data, dict):
            table = [[key, self._format_cell(value, 1, compact, max_str_length)] for key, value in sorted(data.iteritems())]
            return self._format_table(None, table, 0, compact)

        if isinstance(data, (list, tuple)):
            table = []
            headers = []
            keys = set()
            for item in data:
                if isinstance(item, dict):
                    keys.update(item.iterkeys())
            keys = sorted(keys, key=self._key_sorter)
            headers = [self._split_string(key, max_str_length) for key in keys]
            for item in data:
                if isinstance(item, dict):
                    table.append([self._format_cell(item.get(key, ''), 1, compact, max_str_length) for key in keys])
            formatted = self._format_table(headers, table, 0, compact)
            non_dicts = [self._format_cell(item, 1, compact, max_str_length) for item in data if not isinstance(item, dict)]
            if non_dicts:
                formatted += '\n' + self._format_table(None, non_dicts, 0, compact)
            return formatted

        return self._format_cell(data, 1, compact, max_str_length)

    def format(self, data):
        width = self._terminal_size or self._get_terminal_size()[1]
        table = self._format(data, compact=False, max_str_length=None)
        if len(table.split('\n', 1)[0]) <= width:
            return table
        table = self._format(data, compact=False, max_str_length=self._max_str_length)
        if len(table.split('\n', 1)[0]) <= width:
            return table
        table = self._format(data, compact=True, max_str_length=self._max_str_length)
        if len(table.split('\n', 1)[0]) <= width:
            return table
        min_max_str_length = 10
        max_max_str_length = self._max_str_length
        max_str_length = (min_max_str_length + max_max_str_length) / 2
        while min_max_str_length < max_str_length:
            max_str_length = (min_max_str_length + max_max_str_length) / 2
            table = self._format(data, compact=True, max_str_length=max_str_length)
            if len(table.split('\n', 1)[0]) > width:
                max_max_str_length = max_str_length
            else:
                min_max_str_length = max_str_length
        return table

    def _get_terminal_size(self):
        def ioctl_GWINSZ(fd):
            try:
                return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            except:
                pass
        cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
        return cr
