class AdaptiveTableDef(object):
    def __init__(self, widths, depth, compact, force_frames, horizontal_lines, headers):
        self._depth = depth
        self._headers = headers
        self._force_frames = force_frames
        self._horizontal_lines = horizontal_lines
        self._set_separators(widths, depth, compact, force_frames)

    def _set_separators(self, widths, depth, compact, force_frames):
        line_joiner = '|' if compact else ' | '
        line_edges = '%s' if compact else ' %s '
        if (depth == 0 and not compact) or force_frames:
            line_edges = '|%s|' % line_edges
        sep_joiner = '+' if compact else '-+-'
        sep_edges = '%s' if compact else '-%s-'
        if (depth == 0 and not compact) or force_frames:
            sep_edges = '+%s+' % sep_edges
        self.line_format = line_edges % (line_joiner.join(['%%-%ds' % width for width in widths]))
        self._line_separator = sep_edges % (sep_joiner.join(['-' * width for width in widths]))
        self._header_separator = self._line_separator.replace('-', '=')

    def _separator_needed(self, row_index, max_lines, prev_max_lines):
        if self._horizontal_lines:
            return True
        if row_index <= 0:  # before first line
            return self._force_frames or self._depth == 0  # separator if outer table or --force-frames
        if self._depth == 0 and row_index == 0:  # separator before first row
            return True
        if row_index == 1 and self._headers:  # separator after the header
            return True
        return max_lines > 1 or prev_max_lines > 1  # separator between rows with more than one line

    def get_separator(self, row_index, max_lines, prev_max_lines):
        if not self._separator_needed(row_index, max_lines, prev_max_lines):
            return None
        return self._header_separator if row_index == 1 and self._headers else self._line_separator

    def get_end_separator(self):
        return self._line_separator
