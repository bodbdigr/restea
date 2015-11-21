import re
import datetime

import six


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
        for name, field in six.iteritems(fields):
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

    @property
    def required_field_names(self):
        '''
        Returns only required field names
        :returns: required field names (from self.fields)
        :rtype: set
        '''
        return set(
            name for name, field in six.iteritems(self.fields)
            if field.required
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
        for name, value in six.iteritems(data):
            if name not in field_names:
                continue
            cleaned_data[name] = self.fields[name].validate(value)

        for req_field in self.required_field_names:
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

        for setting_name, setting in six.iteritems(self._settings):
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
        if not isinstance(field_value, six.string_types):
            raise FieldSet.Error(
                'Field "{}" is not a string'.format(self._name)
            )
        return field_value


class Regex(String):
    '''
    Regex implements field validation using regex pattern
    '''
    def _validate_pattern(self, option_value, field_value):
        '''
        Validates if given string matches patten or list of patterns. If at
        least one pattern matches validation is passing
        '''
        res = None
        if isinstance(option_value, (list, tuple, set)):
            for pattern in option_value:
                res = re.findall(pattern, field_value, re.IGNORECASE)
                if res:
                    break
        else:
            res = re.findall(option_value, field_value, re.IGNORECASE)

        if not res:
            raise FieldSet.Error(
                'Field value doesn\'t match required pattern'
            )
        return res


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
    def _validate_field(self, field_value):
        try:
            return datetime.datetime.fromtimestamp(field_value / 1000).replace(microsecond=0)
        except TypeError:
            raise FieldSet.Error(
                'Field "{}" can\'t be parsed'.format(self._name)
            )


class Email(String):
    '''
    Email implements Email datatype -> so we can easily use email from wsgi input in our rest resource
    '''

    def _validate_field(self, field_value):
        super(Email, self)._validate_field(field_value)

        message = 'Enter a valid email address in field {}. An example example@example.com'.format(self._name)
        error = self.__validate_email(field_value)
        if not error:
            raise FieldSet.Error(
                message
            )
        return field_value

    def __validate_email(self, field_value):

        user_regex = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
            re.IGNORECASE
        )

        domain_regex = re.compile(
            # max length for domain name labels is 63 characters per RFC
            # 1034
            r'((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z',
            re.IGNORECASE
        )

        if not field_value or '@' not in field_value:
            return False

        user_part, domain_part = field_value.rsplit('@', 1)

        if not user_regex.match(user_part):
            return False

        if not domain_regex.match(domain_part):
            return False
        return True
