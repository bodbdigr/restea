import sys

PY3 = sys.version_info[0] >= 3

if PY3:
    def iteritems(_dict):
        return _dict.items()

    string_types = str
else:
    def iteritems(_dict):
        return _dict.iteritems()

    string_types = (str, unicode)
