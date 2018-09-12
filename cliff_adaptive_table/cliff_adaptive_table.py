from cliff.formatters.base import ListFormatter, SingleFormatter


class AdaptiveTableFormatter(ListFormatter, SingleFormatter):

    def add_argument_group(self, parser):
        pass

    def emit_list(self, column_names, data, stdout, parsed_args):
        combined = [dict(zip(column_names, row)) for row in data]
        import json
        stdout.write(json.dumps(combined))
        stdout.write('\n')
        return

    def emit_one(self, column_names, data, stdout, parsed_args):
        combined = dict(zip(column_names, list(data)))
        import json
        stdout.write(json.dumps(combined))
        stdout.write('\n')
