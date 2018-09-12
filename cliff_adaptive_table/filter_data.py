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


def filter_data(data, columns, greps, reverse_greps, head, tail):
    data = _filter_data(data, greps, reverse_greps)
    data = _filter_columns(data, columns)
    if isinstance(data, list):
        if head:
            data = data[:head]
        if tail:
            data = data[-tail:]
    return data
