import modifier


FILTER_DATA_HELP = {
    'description': 'These modifiers are processed in the following order: grep*, head, tail and finally columns and columns-v',
    'modifiers':
    [
        {
            'modifier': 'grep=<pattern>',
            'description': 'Print only rows where the pattern (regular expression) matches any of the values. Note that the values are searched recursively.',
            'examples':
            [
                'grep=name - Only print rows where one of the values matches \'name\'.',
                'grep=name|nombre - Only print rows where one of the values matches either \'name\' or \'nombre\'.',
                'grep=name grep=nombre - Only print rows that have a value that matches \'name\' and a value that matches \'nombre\'.'
            ]
        },
        {
            'modifier': 'grep-i=<pattern>',
            'description': 'Same as grep, but matching is case-insensitive.'
        },
        {
            'modifier': 'grep-v=<pattern>',
            'description': 'Skip rows that have a value that matches pattern.',
            'examples':
            [
                'grep-v=name - Only print rows where none of the values matches \'name\'.',
                'grep-v=name|nombre - Only print rows where none of the values matches either \'name\' or \'nombre\'.',
                'grep-v=name grep-v=nombre - Print all rows except rows that have a value that matches \'name\' and a value that matches \'nombre\'.'
            ]
        },
        {
            'modifier': [
                'grep-iv=<pattern>',
                'grep-vi=<pattern>'
            ],
            'description': 'same as grep-v, but matching is case-insensitive.'
        },
        {
            'modifier': 'head=<n>',
            'description': 'Only print first n rows.'
        },
        {
            'modifier': 'tail=<n>',
            'description': 'Only print last n rows. Note that tail is processed after head regardless of their order in the command. Thus, if the entire table had 20 rows, head=10 tail=5 means that rows 6-10 are printed (where row number starts at 1).'
        },
        {
            'modifier': 'columns=<pattern>',
            'description': 'Only print columns whose name match pattern (matching is case-insensitive). If repeated, all columns matching any of the patterns will be printed. Thus, columns=id|name is the same as columns=id columns=name (in contradistiction to grep*). Note that the columns modifier is processed after the grep* modifiers, so the matched values might not be printed.'
        },
        {
            'modifier': 'columns-v=<pattern>',
            'description': 'Do not print columns whose name match pattern (matching is case-insensitive). If repeated, all columns matching any of the patterns will be ignored. Thus, columns-v=id|name is the same as columns-v=id columns-v=name (in contradistiction to grep*). Note that the columns-v modifier is processed after the grep* modifiers, so the matched values might not be printed.'
        }
    ],
}


class FilterData(object):
    MODIFIERS = {'grep': modifier.append_regex,
                 'grep-v': modifier.append_regex,
                 'grep-i': modifier.append_case_insensitive_regex,
                 'grep-iv': modifier.append_case_insensitive_regex,
                 'grep-vi': modifier.append_case_insensitive_regex,
                 'columns': modifier.append_case_insensitive_regex,
                 'columns-v': modifier.append_case_insensitive_regex,
                 'head': modifier.to_int,
                 'tail': modifier.to_int}

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
        reverse_greps = self._modifiers.get('grep-v', []) + self._modifiers.get('grep-vi', []) + self._modifiers.get('grep-iv', [])
        data = self._filter_data(data, greps, reverse_greps)
        data = self._filter_columns(data, self._modifiers.get('columns', []), self._modifiers.get('columns-v', []))
        if isinstance(data, list):
            if 'head' in self._modifiers:
                data = data[:self._modifiers['head']]
            if 'tail' in self._modifiers:
                data = data[-self._modifiers['tail']:]
        return data

    def get_modifier_names(self):
        return self.MODIFIERS.keys()

    def help(self):
        return FILTER_DATA_HELP
