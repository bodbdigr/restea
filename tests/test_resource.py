import mock
import nose

from mock import patch

from restpy import errors
from restpy import formats
from restpy.resource import Resource


def test_get_method_name_list():
    req_mock = mock.Mock(method='GET', headers={})
    resource = Resource(req_mock, mock.Mock())
    assert 'list' == resource._get_method_name(has_iden=False)


def test_get_method_name_show():
    req_mock = mock.Mock(method='GET', headers={})
    resource = Resource(req_mock, mock.Mock())
    assert 'show' == resource._get_method_name(has_iden=True)


def test_get_method_name_edit():
    req_mock = mock.Mock(method='PUT', headers={})
    resource = Resource(req_mock, mock.Mock())
    assert 'edit' == resource._get_method_name(has_iden=True)


def test_get_method_name_edit_without_iden():
    req_mock = mock.Mock(method='PUT', headers={})
    resource = Resource(req_mock, mock.Mock())
    nose.tools.assert_raises(
        errors.BadRequestError,
        resource._get_method_name,
        has_iden=False
    )


def test_get_method_name_create():
    req_mock = mock.Mock(method='POST', headers={})
    resource = Resource(req_mock, mock.Mock())
    assert 'create' == resource._get_method_name(has_iden=False)


def test_get_method_name_create_with_id():
    req_mock = mock.Mock(method='POST', headers={})
    resource = Resource(req_mock, mock.Mock())
    nose.tools.assert_raises(
        errors.BadRequestError,
        resource._get_method_name,
        has_iden=True
    )


def test_get_method_name_delete():
    req_mock = mock.Mock(method='DELETE', headers={})
    resource = Resource(req_mock, mock.Mock())
    assert 'delete' == resource._get_method_name(has_iden=True)


def test_get_method_name_unpecefied_method():
    req_mock = mock.Mock(method='HEAD', headers={})
    resource = Resource(req_mock, mock.Mock())
    nose.tools.assert_raises(
        errors.MethodNotAllowedError,
        resource._get_method_name,
        has_iden=True
    )


def test_get_method_name_method_override():
    req_mock = mock.Mock(
        method='POST',
        headers={'HTTP_X_HTTP_METHOD_OVERRIDE': 'PUT'}
    )
    resource = Resource(req_mock, mock.Mock())
    assert 'edit' == resource._get_method_name(has_iden=True)


def test_iden_required_positive():
    resource = Resource(mock.Mock(), mock.Mock())
    assert resource._iden_required('show')
    assert resource._iden_required('edit')
    assert resource._iden_required('delete')


def test_iden_required_negative():
    resource = Resource(mock.Mock(), mock.Mock())
    nose.tools.assert_false(resource._iden_required('create'))
    nose.tools.assert_false(resource._iden_required('list'))


def test_apply_decorators():
    resource = Resource(mock.Mock(), mock.Mock())
    resource.create = mock.MagicMock(return_value={
        'test1': 0,
        'test2': 0
    })

    def dummy_decorator1(func):
        def wrapper(*a, **kw):
            res = func(*a, **kw)
            res['test1'] = 'replacement #1'
            return res
        return wrapper

    def dummy_decorator2(func):
        def wrapper(*a, **kw):
            res = func(*a, **kw)
            res['test2'] = 'replacement #2'
            return res
        return wrapper

    resource.decorators = [dummy_decorator1, dummy_decorator2]
    resource.create = resource._apply_decorators(resource.create)

    expected_values = {'test1': 'replacement #1', 'test2': 'replacement #2'}
    assert resource.create() == expected_values


def test_is_valid_decorator_positive():
    resource = Resource(mock.Mock(), formats.JsonFormat)
    assert resource._is_valid_formatter


def test_is_valid_decorator_negative():
    resource = Resource(mock.Mock(), None)
    nose.tools.assert_false(resource._is_valid_formatter)


def test_error_formatter_valid():
    resource = Resource(mock.Mock(), formats.JsonFormat)
    assert resource._error_formatter == formats.JsonFormat


def test_error_formatter_with_unknown_formatter():
    resource = Resource(mock.Mock(), None)
    assert resource._error_formatter == formats.DEFAULT_FORMATTER


def test_get_method_valid():
    resource = Resource(mock.Mock(), mock.Mock())
    resource.create = mock.Mock(return_value={})
    assert resource._get_method('create') == resource.create


def test_get_method_with_not_existing_method():
    resource = Resource(mock.Mock(), mock.Mock())
    nose.tools.assert_raises(
        errors.BadRequestError,
        resource._get_method,
        'not_exising_method'
    )


@patch.object(formats.JsonFormat, 'serialize')
def test_process_valid(serialize_mock):
    mocked_value = 'mocked_value'
    serialize_mock.return_value = mocked_value

    req_mock = mock.Mock(method='GET', headers={}, data=None)
    resource = Resource(req_mock, formats.JsonFormat)

    resource.show = mock.Mock(return_value={})
    res = resource.process(iden=10)

    assert res == mocked_value


@patch.object(formats.JsonFormat, 'serialize')
def test_process_valid_list(serialize_mock):
    req_mock = mock.Mock(method='GET', headers={}, data=None)
    resource = Resource(req_mock, formats.JsonFormat)


    serialize_mock.return_value = '[]'
    resource.list = mock.Mock(return_value=[])
    res = resource.process()
    assert res == '[]'

    serialize_mock.return_value = '{}'
    resource.show = mock.Mock(return_value={})
    res = resource.process(iden=10)
    assert res == '{}'


def test_process_wrong_formatter():
    req_mock = mock.Mock(method='GET', headers={}, data=None)
    resource = Resource(req_mock, None)
    resource.list = mock.MagicMock(return_value='')

    nose.tools.assert_raises(
        errors.BadRequestError,
        resource.process,
    )


@patch.object(formats.JsonFormat, 'unserialize')
def test_process_unexisting_payload(unserialize_mock):
    req_mock = mock.Mock(method='POST', headers={}, data='data')
    resource = Resource(req_mock, formats.JsonFormat)

    unserialize_mock.side_effect = formats.LoadError()
    resource.create = mock.MagicMock(return_value='')

    nose.tools.assert_raises(
        errors.BadRequestError,
        resource.process,
    )


@patch.object(formats.JsonFormat, 'unserialize')
def test_process_valid_payload(unserialize_mock):
    req_mock = mock.Mock(method='PUT', headers={}, data='{"test": 1}')
    resource = Resource(req_mock, formats.JsonFormat)

    expected_payload = {'test': 1}
    unserialize_mock.return_value = expected_payload
    resource.edit = mock.MagicMock(return_value='')
    resource.process(iden=10)

    assert resource.payload == expected_payload


@patch.object(formats.JsonFormat, 'serialize')
def test_process_error_in_method_should_raise_server_error(serialize_mock):
    req_mock = mock.Mock(method='GET', headers={}, data=None)
    resource = Resource(req_mock, formats.JsonFormat)

    resource.list = mock.MagicMock(side_effect=ValueError('I will raise'))

    nose.tools.assert_raises(
        errors.ServerError,
        resource.process,
    )


@patch.object(formats.JsonFormat, 'serialize')
def test_process_error_in_formatter_serialize_should_raise_server_error(
    serialize_mock
):
    req_mock = mock.Mock(method='GET', headers={}, data=None)
    resource = Resource(req_mock, formats.JsonFormat)

    resource.list = mock.MagicMock(return_value='')
    serialize_mock.side_effect = formats.LoadError()

    nose.tools.assert_raises(
        errors.ServerError,
        resource.process,
    )
