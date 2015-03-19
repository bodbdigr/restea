# TODO Add Decimal, RegexString, List, Mapping fields. Add docs. Add tests


class FieldSet(object):

    class Error(Exception):
        pass

    def __init__(self, **fields):
        self.fields = {}
        for name, field in fields.iteritems():
            field.set_name(name)
            self.fields[name] = field

    def __getitem__(self, key):
        return self.fields[key]

    @property
    def field_names(self):
        return self.fields.keys()

    def validate(self, data):
        field_names = self.field_names
        cleaned_data = {}
        for name, value in data.iteritems():
            if name not in field_names:
                continue
            cleaned_data[name] = self.fields[name].clean_field(value)
        return cleaned_data


class Field(object):
    def __init__(self, **settings):
        self._name = None
        self._required = not settings.pop('optional', False)
        self._settings = {}
        self._settings = settings

    def set_name(self, name):
        self._name = name

    def clean_field(self, value):
        raise NotImplementedError


class Integer(Field):
    def clean_field(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise FieldSet.Error('Field "{}" not a number'.format(self._name))


class String(Field):
    def clean_field(self, value):
        return value
