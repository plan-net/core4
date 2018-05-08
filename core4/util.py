# -*- coding: utf-8 -*-

# def parse_regex_string(regex):
#     parts = regex.split('/')
#     try:
#         pattern = "/".join(parts[1:-1])
#         flags = 0
#         for f in parts[-1].lower():
#             flags = flags | REGEX_FLAG[f]
#     except:
#         raise ConfigurationError, 'invalid regular expression value [%s]' % (
#             regex)
#     return re.compile(pattern, flags)
