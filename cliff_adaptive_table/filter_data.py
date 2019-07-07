import modifier


FILTER_DATA_HELP = {
    'description': 'These modifiers are processed in the following order: grep*, head, tail and finally columns and columns-v.',
    'modifiers':
    [
        {
            'modifier': 'grep=<pattern>',
            'description': 'Displays only those rows containing a value that matches the pattern. The matching is case-sensitive. The pattern can be any regular expression. Note: The values are searched recursively.',
            'examples':
            [
                'grep=name - Displays only those rows containing a value that matches \'name\'.',
                'grep=name|nombre - Displays only those rows containing a value that matches either \'name\' or \'nombre\'.',
                'grep=name grep=nombre - Displays only those rows containing both one value that matches \'name\' and another value that matches \'nombre\'.'
            ]
        },
        {
            'modifier': 'grep-i=<pattern>',
            'description': 'Same as grep, but the matching is case-insensitive.'
        },
        {
            'modifier': 'grep-v=<pattern>',
            'description': 'Displays all rows except those containing any values that match the pattern. The matching is case-sensitive. The pattern can be any regular expression.',
            'examples':
            [
                'grep-v=name - Displays all rows except those that contain a value that matches \'name\'.',
                'grep-v=name|nombre - Displays all rows except those that contain a value that matches either \'name\' or \'nombre\'.',
                'grep-v=name grep-v=nombre - Displays all rows except those that contain both one value that matches \'name\' and another value that matches \'nombre\'.'
            ]
        },
        {
            'modifier': [
                'grep-iv=<pattern>',
                'grep-vi=<pattern>',
                'grep-i-v=<pattern>',
                'grep-v-i=<pattern>'
            ],
            'description': 'Same as grep-v, but the matching is case-insensitive.'
        },
        {
            'modifier': 'head=<n>',
            'description': 'Display only the first n rows.'
        },
        {
            'modifier': 'tail=<n>',
            'description': 'Displays only the last n rows. Thus, if a table had 20 rows, -m head=10 tail=5, would display the last five rows of the first ten, or rows 6-10. Note: tail is processed after head regardless of their order in the command.',
        },
        {
            'modifier': 'columns=<pattern>',
            'description': 'Displays only those columns whose headers match the pattern. The matching is case-insensitive. If repeated, all columns matching any of the patterns will be displayed. The pattern can be any regular expression. Note: The columns modifier is processed after the grep* modifiers, so the matched values might not be displayed.',
            'examples':
            [
                'columns=name - Displays only those columns whose headers match \'name\'.',
                'columns=name|id or \'columns=name columns=id\' (In contrast to grep=pattern) - Displays only those columns whose headers match either \'name\' or \'id\'.',
            ]
        },
        {
            'modifier': 'columns-v=<pattern>',
            'description': 'Displays all columns except those whose headers match the pattern. The matching is case-insensitive. If repeated, all columns matching any of the patterns will not be displayed. The pattern can be any regular expression. Note: The columns* modifiers are processed after the grep* modifiers, so the matched values might not be displayed.',
            'examples':
            [
                'columns-v=name - Displays all columns except those whose headers match \'name\'.',
                'columns-v=name|id or \'columns-v=name columns-v=id\' (In contrast to grep-v=<pattern>) - Displays all columns except those whose headers match either \'name\' or \'id\'.',
            ]
        },
        {
            'modifier': 'sort=[<order>:]<column name>',
            'description': 'Sorts rows according to the values in a specific column. Note: column name must be exact. Order, if given, is either \'a\' or \'A\' for ascending, or \'d\' or \'D\' for descending.',
            'examples':
            [
                'sort=score - Sorts columns according to the values in column \'score\' in ascending order',
                'sort=A:name - Sorts columns according to the values in column \'name\' in ascending order',
                'sort=d:age - Sorts columns according to the values in column \'age\' in descending order',
            ]
        },
    ],
}


class FilterData(object):
    MODIFIERS = {'grep': modifier.append_regex,
                 'grep-v': modifier.append_regex,
                 'grep-i': modifier.append_case_insensitive_regex,
                 'grep-iv': modifier.append_case_insensitive_regex,
                 'grep-vi': modifier.append_case_insensitive_regex,
                 'grep-i-v': modifier.append_case_insensitive_regex,
                 'grep-v-i': modifier.append_case_insensitive_regex,
                 'columns': modifier.append_case_insensitive_regex,
                 'columns-v': modifier.append_case_insensitive_regex,
                 'head': modifier.to_int,
                 'tail': modifier.to_int,
                 'sort': modifier.sort}

    def _filter_data(self, data, greps, reverse_greps):
        def _matches(data, pattern):
            if isinstance(data, dict):
                return any(_matches(value, pattern) for value in data.itervalues())
            if isinstance(data, (list, tuple)):
                return any(_matches(value, pattern) for value in data)
            return pattern.search(str(data))

        def _filter(data, greps, reverse_greps):
            return all(_matches(data, pattern) for pattern in greps) and \
                not (reverse_greps and all(_matches(data, pattern) for pattern in reverse_greps))

        if not greps and not reverse_greps:
            return data
        if isinstance(data, dict):
            return {key: value for key, value in data.iteritems() if _filter(value, greps, reverse_greps)}
        if isinstance(data, (list, tuple)):
            return [value for value in data if _filter(value, greps, reverse_greps)]
        return _filter(value, greps, reverse_greps)

    def _filter_columns(self, data, column_patterns, column_anti_patterns):
        def _filter_columns_in_dict(data, column_patterns, column_anti_patterns):
            if isinstance(data, dict):
                data = {key: value for key, value in data.iteritems() if
                        (not column_patterns or any(pattern.search(key) for pattern in column_patterns)) and
                        (not column_anti_patterns or not any(pattern.search(key) for pattern in column_anti_patterns))}
            return data

        if not column_patterns and not column_anti_patterns:
            return data
        if isinstance(data, (list, tuple)):
            return [_filter_columns_in_dict(value, column_patterns, column_anti_patterns) for value in data]
        else:
            return _filter_columns_in_dict(data, column_patterns, column_anti_patterns)

    def parse_modifiers(self, args):

        self._modifiers, unrecognized_modifiers = modifier.parse_modifiers(self.MODIFIERS, args)
        return unrecognized_modifiers

    def filter_data(self, data):
        greps = self._modifiers.get('grep', []) + self._modifiers.get('grep-i', [])
        reverse_greps = []
        for name in ('grep-v', 'grep-vi', 'grep-iv', 'grep-v-i', 'grep-i-v'):
            reverse_greps.extend(self._modifiers.get(name, []))
        data = self._filter_data(data, greps, reverse_greps)
        data = self._filter_columns(data, self._modifiers.get('columns', []), self._modifiers.get('columns-v', []))
        if isinstance(data, list):
            if 'head' in self._modifiers:
                data = data[:self._modifiers['head']]
            if 'tail' in self._modifiers:
                data = data[-self._modifiers['tail']:]
        sort_by = self._modifiers.get('sort')
        if sort_by:
            reverse, sort_key = sort_by
            if isinstance(data, (list, tuple)) and all(isinstance(row, dict) for row in data):
                data.sort(key=lambda row: row.get(sort_key), reverse=reverse)
        return data

    def get_modifier_names(self):
        return self.MODIFIERS.keys()

    def help(self):
        return FILTER_DATA_HELP
