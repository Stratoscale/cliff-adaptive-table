def csv(value):
    return value.split(',')

def boolean(value):
    return {'yes': True, 'y': True, 't': True, 'true': True,
            'n': False, 'no': False, 'f': False, 'false': False}[value.lower()]

def parse_modifiers(modifiers, args):
    unrecognized = []
    recognized = {}
    for arg in (args or []):
        try:
            key, value = arg.split('=', 1)
            if key in modifiers:
                recognized[key] = modifiers[key](value)
            else:
                unrecognized.append(arg)
        except:
            unrecognized.append(arg)
    return recognized, unrecognized
