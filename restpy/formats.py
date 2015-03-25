import collections
import urlparse
import json
import re


_formatter_registry = {}


class LoadError(Exception):
    '''
    Error raiseed in case serializing or unserializing went wrong
    '''


class FormatterRegistry(type):
    '''
    Registry metaclass. Registers all `restpy.formats.BaseFormat` sublcasses
    in _formatter_registry
    '''
    def __init__(cls, name, bases, dict):
        super(FormatterRegistry, cls).__init__(name, bases, dict)
        if name != 'BaseFormatter':
            _formatter_registry[cls.name] = cls


class BaseFormatter(object):
    '''
    BaseFormatter is base class for different serialization formats
    '''
    __metaclass__ = FormatterRegistry

    @classmethod
    def unserialize(cls, data):
        '''
        Unserializes imcomming data (payload)

        :param data: string - raw data to be unserialized
        :returns: dict -- respesenation of the data in python datastructure
        '''
        raise NotImplementedError

    @classmethod
    def serialize(cls, data):
        '''
        Serializes outgoing data

        :param data: dict - python data structure to be serialized
        :returns: string -- serialized respesenation of the data
        '''
        raise NotImplementedError


class JsonFormat(BaseFormatter):

    name = 'json'
    content_type = 'application/json'

    @classmethod
    def unserialize(cls, data):
        '''
        Unserializes imcomming data (payload)

        :param data: string - raw data to be unserialized
        :returns: dict -- respesenation of the data in python datastructure
        '''
        try:
            return json.loads(data)
        except ValueError:
            raise LoadError

    @classmethod
    def serialize(cls, data):
        '''
        Serializes outgoing data

        :param data: dict - python data structure to be serialized
        :returns: string -- serialized respesenation of the data
        '''
        try:
            return json.dumps(data)
        except ValueError:
            raise LoadError


class FormEncodedFormat(BaseFormatter):

    name = 'html'
    content_type = 'application/x-www-form-urlencoded'

    @classmethod
    def _typecast_form_value(cls, value):
        '''
        Typecasts the format of value in querystring from strng to either int,
        bool, None or if any of those doesn't match leaves value as string

        :param value: string -- value to typecast
        :returns: int or string or bool or None -- retulting type of the value
        after typecasting
        '''
        if not value:
            return ''

        try:
            return int(value)
        except (TypeError, ValueError):
            lower_value = value.lower()
            if lower_value in ('true', 'false'):
                return lower_value == 'true'
            if lower_value in ('null', 'none'):
                return None
            return value

    @classmethod
    def _unserialize_nested_keys(cls, nested_keys, value):
        '''
        Builds a nested node branch. For instance if we have some structure
        like element[level1][level2][level3]=value it would translate it to
        >>> {'level1': {'level2': {'level3': 'value'}

        :param nested_keys: list -- list of nested nodes, for instance
        ['level1', 'level2', 'level3']
        :param value: string -- value to be set for inner key

        :returns: dict -- structure of nested dicts representing
        element[key] notation
        '''
        if not nested_keys:
            return value

        res = root = {}
        while True:
            nested_key = nested_keys.pop(0)
            if len(nested_keys):
                root[nested_key] = {}
                root = root[nested_key]
            else:
                root[nested_key] = cls._typecast_form_value(value)
                break
        return res

    @classmethod
    def _find_nested_keys(cls, query):
        '''
        Finds a nested keys in given query, for instance
        element[level1][level2] would retult ['level1', 'level2']

        :param query: string -- string to find nested nodes pattern
        :returns: list - list of nested nodes found
        '''
        return re.findall('\[(\w+)\]', query)

    @classmethod
    def unserialize(cls, data):
        '''
        Unserializes imcomming data (payload)

        :param data: string - raw data to be unserialized
        :returns: dict -- respesenation of the data in python datastructure
        '''
        parsed_qs = urlparse.parse_qsl(data)
        res = collections.defaultdict(dict)

        for key, value in parsed_qs:
            nested_keys = cls._find_nested_keys(key)
            if nested_keys:
                root_key, _ = key.split('[', 1)
                res[root_key].update(cls._unserialize_nested_keys(
                    nested_keys,
                    value
                ))
            else:
                res[key] = cls._typecast_form_value(value)

        return dict(res)

    @classmethod
    def serialize(cls, data):
        '''
        Serializes outgoing data

        :param data: dict or list -- python data structure to be serialized
        :returns: string -- serialized respesenation of the data
        '''
        # TODO Add serialize
        raise NotImplementedError


def get_formatter(format_name):
    '''
    Factory method returning format class based on it's name
    :param format_name: string -- name of the format
    :returns: either subclass :class: `restpy.formats.BaseFormatter` or None
    '''
    return _formatter_registry.get(format_name)


DEFAULT_FORMATTER = JsonFormat
