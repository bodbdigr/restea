import mock
import pytest
import datetime
from restea.fields import (
    Boolean,
    Dict,
    Field,
    FieldSet,
    Integer,
    List,
    String,
    Regex,
    URL,
    DateTime,
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
    assert fs.required_field_names == set(['field1'])


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

    with pytest.raises(FieldSet.Error) as e:
        fs.validate({'field2': '2'})
    assert 'Field "field1" is missing' in str(e)


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

    with pytest.raises(NotImplementedError):
        f._validate_field('test')


def test_field_get_settings_validator():
    f = Field()
    f._validate_my_setting = mock.Mock()
    assert f._get_setting_validator('my_setting') == f._validate_my_setting


def test_field_get_settings_validator_raise_configration_error():
    f = Field()
    f.set_name('test')

    with pytest.raises(FieldSet.ConfigurationError) as e:
        f._get_setting_validator('my_setting')
    assert 'Setting "my_setting" is ' + \
           'not supported for field "test"' in str(e)


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

    with pytest.raises(FieldSet.Error) as e:
        f.validate('value')
    assert field_error_message in str(e)

    assert not f._validate_my_setting.called


def test_field_validate_raises_on_setting_validation():
    f = Field(my_setting=1)
    f.set_name('test')

    f._validate_field = mock.Mock()
    my_setting_error_message = 'my setting error message'
    f._validate_my_setting = mock.Mock(
        side_effect=FieldSet.Error(my_setting_error_message)
    )

    with pytest.raises(FieldSet.Error) as e:
        f.validate('value')
    assert my_setting_error_message in str(e)

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
        with pytest.raises(FieldSet.Error) as e:
            f._validate_field(fail_val)
        assert 'Field "{}" is not a number'.format(f._name) in str(e)


def test_integer_field_range_success():
    f = Integer()
    assert f._validate_range((1, 10), 1) == 1
    assert f._validate_range((1, 10), 5) == 5
    assert f._validate_range((1, 10), 10) == 10


def test_integer_field_range_fail():
    f = Integer()
    for fail_val in (100, 0, -5):
        with pytest.raises(FieldSet.Error):
            f._validate_range((1, 10), fail_val)


def test_string_validate_max_length():
    f = String()
    f._validate_max_length(4, 'text')


def test_string_validate_max_length_fail():
    f = String()
    with pytest.raises(FieldSet.Error) as e:
        f._validate_max_length(4, 'text1')
    assert 'Field "{}" is longer than expected'.format(f._name) in str(e)


def test_string_validate():
    f = String()
    assert f._validate_field('test') == 'test'


def test_string_validate_not_acceptable_value():
    f = String()
    for fail_val in (10, None, list):
        with pytest.raises(FieldSet.Error) as e:
            f._validate_field(fail_val)
        assert 'Field "{}" is not a string'.format(f._name) in str(e)


def test_regex_validate_pattern():
    p = r'\d{1,3}'
    f = Regex(pattern=p)
    for value in ('123', '0', '10'):
        assert f._validate_pattern(p, value)[0] == value


def test_regex_validate_pattern_use_first_found():
    p = r'\d{1,3}'
    f = Regex(use_first_found=True, pattern=p)
    for value in ('123', '0', '10'):
        assert f._validate_pattern(p, value) == value


def test_regex_validate_pattern_list_patterns():
    p = [r'\d{1,3}', r'[a-z]{2,3}']
    f = Regex(pattern=p)
    for value in ('100', '0', 'te', 'tes'):
        assert f._validate_pattern(p, value)[0] == value


def test_regex_validate_pattern_fail():
    p = r'\d{3}'
    f = Regex(pattern=p)
    for value in ('not_a_number', 'other12thing'):
        with pytest.raises(FieldSet.Error):
            f._validate_pattern(value, p)


def test_regex_validate_pattern_list_patterns_fails():
    p = [r'\d{3}', r'[a-z]{100}']
    f = Regex(pattern=p)
    for value in ('not_a_number', 'other12thing'):
        with pytest.raises(FieldSet.Error):
            f._validate_pattern(p, value)


def test_url_validate_pattern():
    f = URL()
    for value in ('http://google.com/ncr', 'https://www.rebelmouse.com'):
        assert f._validate_pattern(f.regex, value)[0] == value


def test_url_validate_pattern_use_first_found():
    f = URL(use_first_found=True)
    for value in ('http://google.com/ncr', 'https://www.rebelmouse.com'):
        assert f._validate_pattern(f.regex, value) == value


def test_url_validate_fail():
    f = URL()
    for value in ('not_a_url', 'otherthing'):
        with pytest.raises(FieldSet.Error):
            f._validate_pattern(f.regex, value)


def test_boolean_validate_true():
    f = Boolean()
    assert f._validate_field(True) is True


def test_boolean_validate_false():
    f = Boolean()
    assert f._validate_field(False) is False


def test_boolean_validate_non_acceptable_value():
    f = Boolean()
    f.set_name('foo')

    for fail_val in (10, None, [], {}, 'bar'):
        with pytest.raises(FieldSet.Error) as e:
            f._validate_field(fail_val)
        assert 'Field "foo" is not a boolean' in str(e)


def test_datetime_validate_acceptible_value():
    f = DateTime()
    expected_date = datetime.datetime(2015, 10, 6, 18, 29, 19)
    res = f._validate_field(1444148959776)
    print res, ' failed'
    assert res == expected_date


def test_datetime_validate_non_acceptable_value():
    f = DateTime()
    f.set_name('foo')

    for fail_val in (None, 'foobar', []):
        with pytest.raises(FieldSet.Error) as e:
            f._validate_field(fail_val)
        assert 'Field "foo" can\'t be parsed' in str(e)


def test_list_validate_empty():
    element_field = mock.Mock()
    f = List(element_field=element_field)
    assert f.validate([]) == []
    assert element_field.mock_calls == []


def test_list_validate():
    element_field = mock.Mock()
    element_field.validate.side_effect = lambda x: x
    f = List(element_field=element_field)
    assert f.validate(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']
    assert element_field.mock_calls == [
        mock.call.validate('foo'),
        mock.call.validate('bar'),
        mock.call.validate('baz'),
    ]


def test_list_validate_fail():
    def mock_validate(value):
        element_field.validate.side_effect = FieldSet.Error
        return value

    element_field = mock.Mock()
    element_field.validate.side_effect = mock_validate
    f = List(element_field=element_field)
    f.set_name('foo')

    with pytest.raises(FieldSet.Error) as e:
        f.validate(['bar', 7, 'baz'])

    assert 'One of the elements on field "foo" failed to validate' in str(e)
    assert element_field.mock_calls == [
        mock.call.validate('bar'),
        mock.call.validate(7),
    ]


def test_list_non_acceptable_value():
    element_field = mock.Mock()
    f = List(element_field=element_field)
    f.set_name('foo')

    for fail_val in (10, None, {}, 'bar', True):
        with pytest.raises(FieldSet.Error) as e:
            f._validate_field(fail_val)
        assert 'Field "foo" is not a list' in str(e)

    assert element_field.mock_calls == []


def test_dict_validate():
    f = Dict()
    di = {
        'foo': 'bar',
        4: True
    }
    assert f._validate_field(di.copy()) == di


def test_dict_validate_non_acceptable_value():
    f = Dict()
    f.set_name('foo')

    for fail_val in (10, None, [], 'bar', True):
        with pytest.raises(FieldSet.Error) as e:
            f._validate_field(fail_val)
        assert 'Field "foo" is not a dict' in str(e)
