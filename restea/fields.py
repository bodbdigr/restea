class FieldSet(object):
    '''
    FieldSet is a container for :class: `restea.fields.Field`. It registers
    fields and also abstracts out validation.
    '''

    #: error thrown in case of failed validation
    class Error(Exception):
        pass

    #: error thrown in case misconfigured field, for istance if setting
    # can't be found for a given field
    class ConfigurationError(Exception):
        pass

    def __init__(self, **fields):
        '''
        :param **fields: dict -- mapping of field names to
        :class: `restea.fields.Field`
        '''
        self.fields = {}
        for name, field in fields.iteritems():
            field.set_name(name)
            self.fields[name] = field

    @property
    def field_names(self):
        '''
        Returns all field names
        :returns: set -- field names (from self.fields)
        '''
        return set(self.fields.keys())

    @property
    def required_field_names(self):
        '''
        Returns only required field names
        :returns: set -- required field names (from self.fields)
        '''
        return set(
            name for name, field in self.fields.iteritems()
            if field.required
        )

    def validate(self, data):
        '''
        Validates payload input
        :param data: dict -- input playload data to be validated
        :raises restea.fields.FieldSet.Error: field validation faield
        :raises restea.fields.FieldSet.Error: required field missing
        :raises restea.fields.FieldSet.ConfigurationError: misformed field
        :returns: dict -- validated data
        '''
        field_names = self.field_names
        cleaned_data = {}
        for name, value in data.iteritems():
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
        :param **settings: dict -- settings dict
        '''
        self.required = settings.pop('required', False)
        self._name = None
        self._settings = settings

    def set_name(self, name):
        '''
        Sets field name
        :param name: string -- setter for a name
        '''
        self._name = name

    def _validate_field(self, field_value):
        '''
        Validates a field value. Shold be overriden in a child class
        :param field_name: string -- name of the field to be validated
        '''
        raise NotImplementedError

    def _get_setting_validator(self, setting_name):
        '''
        Get a validation for a setting name provided
        :param setting_name: string -- name of the setting
        :raises restea.fields.FieldSet.ConfigurationError: validator method
        is not found for a current class
        :returns: function -- field method handling setting validation
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
        :param field_name: string -- name of the field to be validated
        :returns: dict -- validated data
        '''
        res = self._validate_field(field_value)

        for setting_name, setting in self._settings.iteritems():
            validator_method = self._get_setting_validator(setting_name)
            res = validator_method(setting, res)

        return res


class Integer(Field):
    '''
    Integer implements field validation for numeric values
    '''
    def _validate_field(self, field_value):
        '''
        Validates if field value is numeric
        :param field_name: string -- name of the field to be validated
        :returns: int -- validated value
        '''
        try:
            return int(field_value)
        except (ValueError, TypeError):
            raise FieldSet.Error('Field "{}" not a number'.format(self._name))


class String(Field):
    '''
    String implements field validation for string values
    '''
    def _validate_max_length(self, field_value, option_value):
        '''
        Validates if field value is not longer then
        :param field_name: string -- name of the field to be validated
        :returns: string -- validated value
        '''
        if len(field_value) > option_value:
            raise FieldSet.Error(
                'Field "{}" is longer than expected'.format(self._name)
            )
        return field_value

    def _validate_field(self, field_value):
        '''
        Validates if field value is string
        :param field_name: string -- name of the field to be validated
        :returns: string -- validated value
        '''
        if not isinstance(field_value, basestring):
            raise FieldSet.Error('Field "{}" not a string'.format(self._name))
        return field_value
