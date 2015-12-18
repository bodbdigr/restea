import sys

PY3 = sys.version_info[0] >= 3

if PY3:
    from .py3_resource import Resource  # NOQA
else:
    from .py2_resource import Resource  # NOQA
