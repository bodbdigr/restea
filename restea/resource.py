import six

if six.PY2:
    from .py2_resource import Resource

if six.PY3:
    from .py3_resource import Resource  # NOQA
