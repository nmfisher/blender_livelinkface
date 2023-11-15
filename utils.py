import re

def case_independent_compare(*strings):
    if len(strings) < 2:
        return False

    def parse_string(s):
        # \W matches any non-word character, equivalent to [^a-zA-Z0-9_]
        return [item for item in re.split(r'(?=[A-Z])|-| |_|\W', s) if item and not re.match(r'^\W$', item)]

    def format_string_array(arr):
        return ''.join(arr).lower()

    base_string = format_string_array(parse_string(strings[0]))

    for string in strings[1:]:
        if format_string_array(parse_string(string)) != base_string:
            return False

    return True