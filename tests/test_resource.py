import mock
import nose

from restpy import errors
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
