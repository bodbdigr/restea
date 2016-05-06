import datetime
import json
import future.utils
import time


_formatter_registry = {}


class LoadError(Exception):
    '''
    Error raised in case serializing or unserializing went wrong
    '''


class FormatterRegistry(type):
    '''
    Registry metaclass. Registers all `restea.formats.BaseFormat` subclasses
    in _formatter_registry
    '''
    def __init__(cls, name, bases, dict):
        '''
        :param name: name of the formatter class
        :type name: str
        :param bases: base classes for formatter
        :type name: tuple
        :param dict: __dict__ for the formatter class
        :type name: dict
        '''
        super(FormatterRegistry, cls).__init__(name, bases, dict)
        if name != 'BaseFormatter':
            _formatter_registry[cls.name] = cls


class BaseFormatter(future.utils.with_metaclass(FormatterRegistry, object)):
    '''
    BaseFormatter is base class for different serialization formats
    '''

    @classmethod
    def unserialize(cls, data):
        '''
        Unserializes incoming data (payload)

        :param data: raw data to be unserialized
        :type data: str
        :returns: respresentation of the data in Python data structure
        :rtype: dict
        '''
        raise NotImplementedError

    @classmethod
    def serialize(cls, data):
        '''
        Serializes outgoing data

        :param data: Python data structure to be serialized
        :type data: dict, list, str
        :returns: serialized representation of the data
        :rtype: str
        '''
        raise NotImplementedError


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            encoded = int(time.mktime(obj.timetuple()))
        else:
            encoded = json.JSONEncoder.default(self, obj)

        return encoded


class JsonFormat(BaseFormatter):

    name = 'json'
    content_type = 'application/json'

    @classmethod
    def unserialize(cls, data):
        '''
        Unserializes incomming data (payload)

        :param data: raw data to be unserialized
        :type data: str
        :returns: representation of the data in Python data structure
        :rtype: dict
        '''
        try:
            return json.loads(data)
        except ValueError:
            raise LoadError

    @classmethod
    def serialize(cls, data):
        '''
        Serializes outgoing data

        :param data: Python data structure to be serialized
        :type data: dict, list, str
        :returns: serialized representation of the data
        :rtype: str
        '''
        try:
            return json.dumps(data, cls=DateTimeEncoder)
        except ValueError:
            raise LoadError


def get_formatter(format_name):
    '''
    Factory method returning format class based on its name
    :param format_name: name of the format
    :type format_name: str
    :returns: formatter object or None
    :rtype: NoneType, :class: `restea.formats.BaseFormatter`
    '''
    return _formatter_registry.get(format_name)


DEFAULT_FORMATTER = JsonFormat
