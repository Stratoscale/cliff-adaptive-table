import re


def csv(recognized, key, value):
    recognized[key] = value.split(',')


def boolean(recognized, key, value):
    recognized[key] = {'yes': True, 'y': True, 't': True, 'true': True,
                       'n': False, 'no': False, 'f': False, 'false': False}[value.lower()]


def to_int(recognized, key, value):
    recognized[key] = int(value)


def to_str(recognized, key, value):
    recognized[key] = value


def append_regex(recognized, key, value, flags=0):
    pattern = re.compile(value, flags)
    if key not in recognized:
        recognized[key] = []
    recognized[key].append(pattern)


def sort(recognized, key, value):
    tokens = value.split(':', 1)
    if len(tokens) > 1:
        assert tokens[0] in ('a', 'A', 'd', 'D')
    else:
        tokens = ['a', tokens[0]]
    recognized[key] = (tokens[0] in ('d', 'D'), tokens[1])


def append_case_insensitive_regex(recognized, key, value):
    append_regex(recognized, key, value, re.IGNORECASE)


def parse_modifiers(modifiers, args):
    unrecognized = []
    recognized = {}
    for arg in (args or []):
        try:
            key, value = arg.split('=', 1)
            if key in modifiers:
                modifiers[key](recognized, key, value)
            else:
                unrecognized.append(arg)
        except:
            unrecognized.append(arg)
    return recognized, unrecognized
