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
            'subb5': [{'a': 1}, {'b': 2}]
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


def test_get_formatter():
    cls = mock.Mock(spec=formats.BaseFormatter)
    with patch.dict(formats._formatter_registry, {'a': cls}, clear=True):
        assert formats.get_formatter('a') == cls


def test_get_formatter_unexisting():
    with patch.dict(formats._formatter_registry, {}, clear=True):
        assert formats.get_formatter('a') is None
