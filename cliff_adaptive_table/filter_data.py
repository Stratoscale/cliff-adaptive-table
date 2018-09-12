import modifier

def _filter_data(data, greps, reverse_greps):
    def _matches(data, pattern):
        if isinstance(data, dict):
            return any(_matches(value, pattern) for value in data.itervalues())
        if isinstance(data, (list, tuple)):
            return any(_matches(value, pattern) for value in data)
        return pattern.search(str(data))

    def _filter(data, greps, reverse_greps):
        return all(_matches(value, pattern) for pattern in greps) and \
            not (reverse_greps and all(_matches(value, pattern) for pattern in reverse_greps))

    if not greps and not reverse_greps:
        return data
    if isinstance(data, dict):
        return {key: value for key, value in data.iteritems() if _filter(value, greps, reverse_greps)}
    if isinstance(data, (list, tuple)):
        return [value for value in data if _filter(value, greps, reverse_greps)]
    return _filter(value, greps, reverse_greps)


def _filter_columns(data, column_patterns):
    def _filter_columns(data, column_patterns):
        if isinstance(data, dict):
            data = {key: value for key, value in data.iteritems() if any(pattern.search(key) for pattern in column_patterns)}
        return data

    if not column_patterns:
        return data
    if isinstance(data, (list, tuple)):
        return [_filter_columns(value, column_patterns) for value in data]
    else:
        return _filter_columns(data, column_patterns)


def parse_modifiers(args):
    MODIFIERS = {'grep': modifier.append_regex,
                 'grep-v': modifier.append_case_insensitive_regex,
                 'grep-i': modifier.append_regex,
                 'grep-iv': modifier.append_case_insensitive_regex,
                 'grep-vi': modifier.append_case_insensitive_regex,
                 'columns': modifier.append_regex,
                 'head': modifier.to_int,
                 'tail': modifier.to_int}

    return modifier.parse_modifiers(MODIFIERS, args)


def filter_data(data, modifiers):
    greps = modifiers.get('grep', []) + modifiers.get('grep-i', [])
    reverse_greps = modifiers.get('grep-v', []) + modifiers.get('grep-vi', []) + modifiers.get('grep-iv', [])
    data = _filter_data(data, greps, reverse_greps)
    data = _filter_columns(data, modifiers.get('columns'))
    if isinstance(data, list):
        if 'head' in modifiers:
            data = data[:modifiers['head']]
        if 'tail' in modifiers:
            data = data[-modifiers['tail']:]
    return data
