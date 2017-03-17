from past.builtins import basestring

import re
import datetime


class FieldSet(object):
    '''
    FieldSet is a container for :class: `restea.fields.Field`. It registers
    fields and also abstracts out validation.
    '''

    #: error thrown in case of failed validation
    class Error(Exception):
        pass

    #: error thrown in case misconfigured field, for instance if setting
    # can't be found for a given field
    class ConfigurationError(Exception):
        pass

    def __init__(self, **fields):
        '''
        :param **fields: mapping of field names to
        :type **fields: dict
        :class: `restea.fields.Field`
        '''
        self.fields = {}
        for name, field in fields.items():
            field.set_name(name)
            self.fields[name] = field

    @property
    def field_names(self):
        '''
        Returns all field names
        :returns: field names (from self.fields)
        :rtype: set
        '''
        return set(self.fields.keys())

    def get_required_field_names(self, data):
        '''
        Returns only required field names
        :returns: required field names (from self.fields)
        :rtype: set
        '''
        def is_required_field(field, data):
            if callable(field.required):
                return field.required(data)
            else:
                return field.required

        return set(
            name for name, field in self.fields.items()
            if is_required_field(field, data)
        )

    def validate(self, data):
        '''
        Validates payload input
        :param data: input playload data to be validated
        :type data: dict
        :raises restea.fields.FieldSet.Error: field validation failed
        :raises restea.fields.FieldSet.Error: required field missing
        :raises restea.fields.FieldSet.ConfigurationError: badformed field
        :returns: validated data
        :rtype: dict
        '''
        field_names = self.field_names
        cleaned_data = {}
        for name, value in data.items():
            if name not in field_names:
                continue
            cleaned_data[name] = self.fields[name].validate(value)

        for req_field in self.get_required_field_names(cleaned_data):
            if req_field not in cleaned_data:
                raise self.Error('Field "{}" is missing'.format(req_field))

        return cleaned_data


class Field(object):
    '''
    Base class for fields. Implements base functionality leaving concrete
    validation strategy to child classes
    '''
    def __init__(self, **settings):
        '''
        :param **settings: settings dict
        :type **settings: dict
        '''
        self.required = settings.pop('required', False)
        self.null = settings.pop('null', False)
        self._name = None
        self._settings = settings

    def set_name(self, name):
        '''
        Sets field name
        :param name: setter for a name
        :type name: str
        '''
        self._name = name

    def _validate_field(self, field_value):
        '''
        Validates a field value. Should be overriden in a child class
        :param field_name: name of the field to be validated
        :type field_name: str
        '''
        raise NotImplementedError

    def _get_setting_validator(self, setting_name):
        '''
        Get a validation for a setting name provided
        :param setting_name: name of the setting
        :type setting_name: str
        :raises restea.fields.FieldSet.ConfigurationError: validator method
        is not found for a current class
        :returns: field method handling setting validation
        :rtype: function
        '''
        validator_method_name = '_validate_{}'.format(setting_name)

        if not hasattr(self, validator_method_name):
            raise FieldSet.ConfigurationError(
                'Setting "{}" is not supported for field "{}"'.format(
                    setting_name, self._name
                )
            )
        return getattr(self, validator_method_name)

    def validate(self, field_value):
        '''
        Validates as field including settings validation
        :param field_name: name of the field to be validated
        :type field_name: str
        :returns: validated data
        :rtype: dict
        '''
        if self.null and field_value is None:
            return None

        res = self._validate_field(field_value)

        for setting_name, setting in self._settings.items():
            validator_method = self._get_setting_validator(setting_name)
            res = validator_method(setting, res)

        return res


class Integer(Field):
    '''
    Integer implements field validation for numeric values
    '''
    def _validate_range(self, option_value, field_value):
        '''
        Validates if field value is not longer than
        :param field_name: name of the field to be validated
        :type field_name: str
        :returns: validated value
        :rtype: str
        '''
        min_val, max_val = option_value
        if not min_val <= field_value <= max_val:
            raise FieldSet.Error(
                'Value not in bounds for {}'.format(self._name)
            )
        return field_value

    def _validate_field(self, field_value):
        '''
        Validates if field value is numeric
        :param field_name: name of the field to be validated
        :type field_name: str
        :returns: validated value
        :rtype: int
        '''
        try:
            return int(field_value)
        except (ValueError, TypeError):
            raise FieldSet.Error(
                'Field "{}" is not a number'.format(self._name)
            )


class String(Field):
    '''
    String implements field validation for string values
    '''
    def _validate_max_length(self, option_value, field_value):
        '''
        Validates if field value is not longer then
        :param field_name: name of the field to be validated
        :type field_name: str
        :returns: validated value
        :rtype: str
        '''
        if field_value and len(field_value) > option_value:
            raise FieldSet.Error(
                'Field "{}" is longer than expected'.format(self._name)
            )
        return field_value

    def _validate_field(self, field_value):
        '''
        Validates if field value is string
        :param field_name: name of the field to be validated
        :type field_name: str
        :returns: validated value
        :rtype: str
        '''
        if not isinstance(field_value, basestring):
            raise FieldSet.Error(
                'Field "{}" is not a string'.format(self._name)
            )
        return field_value


class Regex(String):
    '''
    Regex implements field validation using regex pattern
    '''
    error_message = 'Field value doesn\'t match required pattern'

    def __init__(self, **settings):
        self.__use_first_found = settings.pop('use_first_found', False)
        super(Regex, self).__init__(**settings)

    def _validate_pattern(self, option_value, field_value):
        '''
        Validates if given string matches patten or list of patterns. If at
        least one pattern matches validation is passing
        '''
        res = None
        if isinstance(option_value, basestring):
            res = re.findall(option_value, field_value, re.IGNORECASE)
        else:
            for pattern in option_value:
                res = re.findall(pattern, field_value, re.IGNORECASE)
                if res:
                    break

        if not res:
            raise FieldSet.Error(self.error_message)
        if self.__use_first_found:
            return res[0]
        return res


class URL(Regex):
    '''
    URL implements field validation for URLs
    '''
    regex = (
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|'
        r'[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$'
    )
    error_message = 'Field value is not a URL'

    def __init__(self, **settings):
        settings['pattern'] = self.regex
        super(URL, self).__init__(**settings)


class Email(String):
    '''
    Email implements field validation for emails
    '''
    error_message = '"%s" is not a valid email'
    pattern = r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*' \
        '(\.[a-z]{2,16})$'

    def _validate_field(self, field_value):
        if not re.match(self.pattern, field_value, re.IGNORECASE):
            raise FieldSet.Error(self.error_message % field_value)

        return field_value


class Boolean(Field):
    '''
    Boolean implements field validation for boolean values
    '''
    def _validate_field(self, field_value):
        if not isinstance(field_value, bool):
            raise FieldSet.Error(
                'Field "{}" is not a boolean'.format(self._name)
            )
        return field_value


class List(Field):
    '''
    List implements field validation for list values
    '''
    def _validate_field(self, field_value):
        if not isinstance(field_value, list):
            raise FieldSet.Error(
                'Field "{}" is not a list'.format(self._name)
            )
        return field_value

    def _validate_element_field(self, element_field, field_value):
        try:
            return [
                element_field.validate(el) for el in field_value
            ]
        except FieldSet.Error:
            raise FieldSet.Error(
                'One of the elements on field "{}" failed to validate'.format(
                    self._name
                )
            )


class Dict(Field):
    '''
    Dict implements field validation for dict values
    '''
    def _validate_field(self, field_value):
        if not isinstance(field_value, dict):
            raise FieldSet.Error(
                'Field "{}" is not a dict'.format(self._name)
            )
        return field_value


class DateTime(Field):
    '''
    DateTime implements field validation for timestamps and cast into date obj
    '''
    def __init__(self, **settings):
        self.__ms_precision = settings.pop('ms_precision', True)
        super(DateTime, self).__init__(**settings)

    def _validate_field(self, field_value):
        try:
            if self.__ms_precision:
                field_value /= 1000.00
            return datetime.datetime.utcfromtimestamp(field_value)
        except TypeError:
            raise FieldSet.Error(
                'Field "{}" can\'t be parsed'.format(self._name)
            )


class CommaSeparatedListField(String):
    def __init__(
            self, limit_per_request=30, cast_func=str, separator=';',
            **settings
    ):
        super(CommaSeparatedListField, self).__init__(**settings)
        self.limit_per_request = limit_per_request
        self.cast_func = cast_func
        self.separator = separator

    def _validate_field(self, field_value):
        """
        :type field_value: str
        :rtype: list(T)
        """
        try:
            super(CommaSeparatedListField, self)._validate_field(field_value)
            parsed_list = list(map(
                self.cast_func, field_value.split(self.separator)
            ))
        except (TypeError, ValueError, FieldSet.Error):
            raise FieldSet.Error(
                'Field "{}" can\'t be parsed as a list'.format(self._name)
            )

        if len(parsed_list) > self.limit_per_request:
            raise FieldSet.Error(
                'Field "{}" has more items than allowed '
                'in the settings'.format(self._name)
            )

        return parsed_list
