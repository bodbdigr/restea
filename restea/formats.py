import json


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
        Unserializes incoming data (payload)

        :param data: string - raw data to be unserialized
        :returns: dict -- respresentation of the data in Python data structure
        '''
        raise NotImplementedError

    @classmethod
    def serialize(cls, data):
        '''
        Serializes outgoing data

        :param data: dict - Python data structure to be serialized
        :returns: string -- serialized representation of the data
        '''
        raise NotImplementedError


class JsonFormat(BaseFormatter):

    name = 'json'
    content_type = 'application/json'

    @classmethod
    def unserialize(cls, data):
        '''
        Unserializes incomming data (payload)

        :param data: string - raw data to be unserialized
        :returns: dict -- representation of the data in Python data structure
        '''
        try:
            return json.loads(data)
        except ValueError:
            raise LoadError

    @classmethod
    def serialize(cls, data):
        '''
        Serializes outgoing data

        :param data: dict - Python data structure to be serialized
        :returns: string -- serialized representation of the data
        '''
        try:
            return json.dumps(data)
        except ValueError:
            raise LoadError


def get_formatter(format_name):
    '''
    Factory method returning format class based on its name
    :param format_name: string -- name of the format
    :returns: either subclass :class: `restea.formats.BaseFormatter` or None
    '''
    return _formatter_registry.get(format_name)


DEFAULT_FORMATTER = JsonFormat
