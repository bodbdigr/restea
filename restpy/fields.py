# TODO Add Decimal, RegexString, List, Mapping fields. Add docs. Add tests


class FieldSet(object):
    class Error(Exception):
        pass

    class ConfigurationError(Exception):
        pass

    def __init__(self, **fields):
        self.fields = {}
        for name, field in fields.iteritems():
            field.set_name(name)
            self.fields[name] = field

    @property
    def field_names(self):
        return set(self.fields.keys())

    @property
    def required_field_names(self):
        return set(
            name for name, field in self.fields.iteritems()
            if field.required
        )

    def validate(self, data):
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
    def __init__(self, **settings):
        self.required = settings.pop('required', False)
        self._name = None
        self._settings = settings

    def set_name(self, name):
        self._name = name

    def _validate_field(self, field_value):
        raise NotImplementedError

    def _get_setting_validator(self, setting_name):
        validator_method_name = '_validate_{}'.format(setting_name)

        if not hasattr(self, validator_method_name):
            raise FieldSet.ConfigurationError(
                'Setting "{}" is not supported for field "{}"'.format(
                    setting_name, self._name
                )
            )
        return getattr(self, validator_method_name)

    def validate(self, field_value):
        res = self._validate_field(field_value)

        for setting_name, setting in self._settings.iteritems():
            validator_method = self._get_setting_validator(setting_name)
            res = validator_method(setting, res)

        return res


class Integer(Field):
    def _validate_field(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise FieldSet.Error('Field "{}" not a number'.format(self._name))


class String(Field):

    def _validate_max_length(self, field_value, option_value):
        if len(field_value) > option_value:
            raise FieldSet.Error(
                'Field "{}" is longer than expected'.format(self._name)
            )
        return field_value

    def _validate_field(self, value):
        if not isinstance(value, basestring):
            raise FieldSet.Error('Field "{}" not a string'.format(self._name))
        return value
