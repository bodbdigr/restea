import json
import mock
from mock import patch
from restpy import formats


@patch.object(formats, '_formatter_registry')
def test_formatter_registry(registry_mock):
    A = formats.FormatterRegistry(
        'A', (formats.BaseFormatter,), {'name': 'a'}
    )
    registry_mock.__setitem__.assert_called_with('a', A)


def test_base_formatter_interface():
    assert hasattr(formats.BaseFormatter, 'serialize')
    assert hasattr(formats.BaseFormatter, 'unserialize')


test_data = {
    'test': 1,
    'test2': {
        'sub1': 1,
        'sub2': 2,
        'sub3': {
            'subb4': 3,
            # 'subb5': [{'a': 1}, {'b': 2}] # Add test lists laster on
        }
    }
}


def test_json_format_params():
    assert formats.JsonFormat.name == 'json'
    assert formats.JsonFormat.content_type == 'application/json'


def test_json_format_unserialize():
    assert formats.JsonFormat.unserialize(json.dumps(test_data)) == test_data


def test_json_format_serialize():
    assert formats.JsonFormat.serialize(test_data) == json.dumps(test_data)


def test_form_encoded_format_params():
    assert formats.FormEncodedFormat.name == 'html'
    expected_type = 'application/x-www-form-urlencoded'
    assert formats.FormEncodedFormat.content_type == expected_type


serialized_form = (
    'test=1&test2[sub1]=1&test2[sub2]=2&test2[sub3][subb4]=3'
    # '&test2[sub3][subb5][][a]=1&test2[sub3][subb5][][b]=2'
)


def test_form_encoded_format_unserialize():
    assert formats.FormEncodedFormat.unserialize(serialized_form) == test_data


def test_form_encoded_format_serialize():
    # TODO Add after serialize function is reader for form encoded format
    # assert formats.FormEncodedFormat.serialize(test_data) == serialized_form
    pass


def test_find_nested_keys():
    input_val = 'test[sub1][sub2][sub3]=res'
    cls = formats.FormEncodedFormat
    assert cls._find_nested_keys(input_val) == ['sub1', 'sub2', 'sub3']


def test_find_nested_keys_empty():
    input_val = 'test=res'
    cls = formats.FormEncodedFormat
    assert cls._find_nested_keys(input_val) == []


def test_unserialize_nested_keys():
    cls = formats.FormEncodedFormat
    expected = {
        'test1': {
            'test2': {
                'test3': 100
            }
        }
    }
    nested_keys = ['test1', 'test2', 'test3']
    assert cls._unserialize_nested_keys(nested_keys, 100) == expected


def test_unserialize_nested_keys_empty():
    cls = formats.FormEncodedFormat
    assert cls._unserialize_nested_keys([], 100) == 100


def test_typecast_form_value_string():
    cls = formats.FormEncodedFormat
    assert cls._typecast_form_value('string') == 'string'


def test_typecast_form_value_int():
    cls = formats.FormEncodedFormat
    assert cls._typecast_form_value('100') == 100
    assert cls._typecast_form_value('010') == 10


def test_typecast_form_value_bool():
    cls = formats.FormEncodedFormat
    assert cls._typecast_form_value('TruE')
    assert not cls._typecast_form_value('fAlse')


def test_typecast_form_value_null():
    cls = formats.FormEncodedFormat
    assert cls._typecast_form_value('null') is None
    assert cls._typecast_form_value('noNe') is None


def test_typecast_form_value_no_data_passed():
    cls = formats.FormEncodedFormat
    assert cls._typecast_form_value(None) == ''


def test_get_formatter():
    cls = mock.Mock(spec=formats.BaseFormatter)
    with patch.dict(formats._formatter_registry, {'a': cls}, clear=True):
        assert formats.get_formatter('a') == cls


def test_get_formatter_unexisting():
    with patch.dict(formats._formatter_registry, {}, clear=True):
        assert formats.get_formatter('a') is None
