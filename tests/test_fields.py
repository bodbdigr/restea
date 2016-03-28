import mock
import nose
from restea.fields import (
    Field,
    FieldSet,
    Integer,
    String,
    Regex,
)


def create_field_set_helper(no_fields=False):
    if no_fields:
        return FieldSet(), None, None

    f1 = mock.Mock(spec=Field())
    f2 = mock.Mock(spec=Field())
    return FieldSet(field1=f1, field2=f2), f1, f2


def test_field_set_init():
    fs, f1, f2 = create_field_set_helper()
    assert fs.fields == {'field1': f1, 'field2': f2}
    f1.set_name.assert_called_with('field1')
    f2.set_name.assert_called_with('field2')


def test_feild_set_field_names():
    fs, _, _ = create_field_set_helper()
    assert fs.field_names == set(['field1', 'field2'])


def test_feild_set_field_names_empty():
    fs, _, _ = create_field_set_helper(no_fields=True)
    assert fs.field_names == set()


def test_field_set_required_fields():
    fs, f1, f2 = create_field_set_helper()
    f1.required = True
    f2.required = False
    assert fs.get_required_field_names({}) == set(['field1'])


def test_field_set_required_fields_callable():
    fs, f1, f2 = create_field_set_helper()

    def foo(data):
        return data.get('field2') == 0
    f1.required = foo
    f2.required = False
    assert fs.get_required_field_names({'field2': 0}) == set(['field1'])
    assert fs.get_required_field_names({}) == set([])

    f1.required = lambda data: data.get('field2') == 0
    f2.required = False
    assert fs.get_required_field_names({'field2': 0}) == set(['field1'])
    assert fs.get_required_field_names({}) == set([])

def test_field_set_validate():
    fs, f1, f2 = create_field_set_helper()
    f1.validate.return_value = 1
    f2.validate.return_value = 2
    res = fs.validate({'field1': '1', 'field2': '2', 'field3': 'wrong!'})

    assert res == {'field1': 1, 'field2': 2}
    f1.validate.assert_called_with('1')
    f2.validate.assert_called_with('2')


def test_feild_set_validate_requred_fields_missing():
    fs, f1, _ = create_field_set_helper()
    f1.requred = True

    nose.tools.assert_raises_regexp(
        FieldSet.Error,
        'Field "field1" is missing',
        fs.validate,
        {'field2': '2'}
    )


def test_field_init():
    f = Field(setting1=1, setting2=2, required=True)
    assert f._name is None
    assert f._settings == {'setting1': 1, 'setting2': 2}
    assert f.required


def test_feld_init_not_required():
    f = Field(setting1=1)
    assert not f.required


def test_field_set_name():
    f = Field()
    f.set_name('test')
    assert f._name == 'test'


def test_field_validate_field_base_should_be_abstract():
    f = Field()
    nose.tools.assert_raises(
        NotImplementedError,
        f._validate_field,
        'test'
    )


def test_field_get_settings_validator():
    f = Field()
    f._validate_my_setting = mock.Mock()
    assert f._get_setting_validator('my_setting') == f._validate_my_setting


def test_field_get_settings_validator_raise_configration_error():
    f = Field()
    f.set_name('test')
    nose.tools.assert_raises_regexp(
        FieldSet.ConfigurationError,
        'Setting "my_setting" is not supported for field "test"',
        f._get_setting_validator,
        'my_setting'
    )


def test_field_validate():
    f = Field(my_setting=1)
    f.set_name('test')

    f._validate_field = mock.Mock(return_value='value')
    f._validate_my_setting = mock.Mock(return_value='value')

    assert f.validate('value') == 'value'

    f._validate_field.assert_called_with('value')
    f._validate_my_setting.assert_called_with(1, 'value')


def test_field_validate_raises_on_field_validation():
    f = Field(my_setting=1)
    f.set_name('test')

    field_error_message = 'Field error message'
    f._validate_field = mock.Mock(
        side_effect=FieldSet.Error(field_error_message)
    )
    f._validate_my_setting = mock.Mock()

    nose.tools.assert_raises_regexp(
        FieldSet.Error,
        field_error_message,
        f.validate,
        'value'
    )
    assert not f._validate_my_setting.called


def test_field_validate_raises_on_setting_validation():
    f = Field(my_setting=1)
    f.set_name('test')

    f._validate_field = mock.Mock()
    my_setting_error_message = 'my setting error message'
    f._validate_my_setting = mock.Mock(
        side_effect=FieldSet.Error(my_setting_error_message)
    )

    nose.tools.assert_raises_regexp(
        FieldSet.Error,
        my_setting_error_message,
        f.validate,
        'value'
    )
    f._validate_field.assert_called_with('value')


def test_integer_field_validate():
    f = Integer()
    assert f._validate_field(1000) == 1000


def test_integer_field_validate_decimal():
    f = Integer()
    assert f._validate_field(10.10) == 10


def test_integer_field_validate_numberic_str():
    f = Integer()
    assert f._validate_field('10') == 10


def test_integer_field_validate_non_acceptable_value():
    f = Integer()
    for fail_val in ('should not work', None, '10.10'):
        nose.tools.assert_raises_regexp(
            FieldSet.Error,
            'Field "{}" is not a number'.format(f._name),
            f._validate_field,
            fail_val
        )


def test_integer_field_range_success():
    f = Integer()
    assert f._validate_range(1, (1, 10)) == 1
    assert f._validate_range(5, (1, 10)) == 5
    assert f._validate_range(10, (1, 10)) == 10


def test_integer_field_range_fail():
    f = Integer()
    for fail_val in (100, 0, -5):
        nose.tools.assert_raises(
            FieldSet.Error,
            f._validate_range,
            fail_val,
            (1, 10)
        )


def test_string_validate_max_length():
    f = String()
    f._validate_max_length('text', 4)


def test_string_validate_max_length_fail():
    f = String()
    nose.tools.assert_raises_regexp(
        FieldSet.Error,
        'Field "{}" is longer than expected'.format(f._name),
        f._validate_max_length,
        'text1', 4
    )


def test_string_validate():
    f = String()
    assert f._validate_field('test') == 'test'


def test_string_validate_not_acceptable_value():
    f = String()
    for fail_val in (10, None, list):
        nose.tools.assert_raises_regexp(
            FieldSet.Error,
            'Field "{}" is not a string'.format(f._name),
            f._validate_field,
            fail_val
        )


def test_regex_validate_pattern():
    p = r'\d{1,3}'
    f = Regex(patten=p)
    for value in ('123', '0', '10'):
        assert f._validate_pattern(value, p)[0] == value


def test_regex_validate_pattern_list_pattrens():
    p = [r'\d{1,3}', r'[a-z]{2,3}']
    f = Regex(patten=p)
    for value in ('100', '0', 'te', 'tes'):
        assert f._validate_pattern(value, p)[0] == value


def test_regex_validate_pattern_fail():
    p = r'\d{3}'
    f = Regex(patten=p)
    for value in ('not_a_number', 'other12thing'):
        nose.tools.assert_raises(
            FieldSet.Error,
            f._validate_pattern,
            value, p
        )


def test_regex_validate_pattern_list_pattrens_fails():
    p = [r'\d{3}', r'[a-z]{100}']
    f = Regex(patten=p)
    for value in ('not_a_number', 'other12thing'):
        nose.tools.assert_raises(
            FieldSet.Error,
            f._validate_pattern,
            value, p
        )
