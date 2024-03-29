import six

from wheezy.http import HTTPResponse
from wheezy.routing import url
from wheezy.http.comp import bton

from restea.adapters.base import (
    BaseResourceWrapper,
    BaseRequestWrapper,
)
from restea.errors import BadRequestError


class WheezyRequestWrapper(BaseRequestWrapper):
    '''
    Object wrapping Wheezy web request object.
    '''
    @property
    def method(self):
        '''
        Returns a payload sent to server

        :returns: string -- raw value of payload sent to server
        '''
        return self._original_request.method

    @property
    def headers(self):
        '''
        Returns a headers dict

        :returns: dict -- received request headers
        '''
        return self._original_request.environ

    def get(self, value):
        '''
        Returns HTTP method for the current request

        :returns: string -- HTTP method name
        '''
        return self._original_request.get_param(value)

    @property
    def data(self):
        '''
        Returns a value from the HTTP GET "map"

        :param value: string -- key from GET
        :returns: string -- value from GET or None if anything is found
        '''
        orig_req = self._original_request
        method = orig_req.method.lower()
        if method == 'get':
            return orig_req.query
        environ = orig_req.environ
        cl = environ['CONTENT_LENGTH']
        icl = int(cl)
        if icl > orig_req.options['MAX_CONTENT_LENGTH']:
            raise BadRequestError('Maximum content length exceeded')
        fp = environ['wsgi.input']
        fp.seek(0)
        ret = bton(fp.read(icl), orig_req.encoding)
        fp.seek(0)
        return ret


class WheezyResourceRouter(BaseResourceWrapper):
    '''
    Wraps over Wheezy web views, implements Wheezy web view API and creates
    routing in the Wheezy web urlrouter format
    '''
    request_wrapper_class = WheezyRequestWrapper

    def prepare_response(self, content, status_code, content_type, headers):
        response = HTTPResponse(content_type=content_type)
        response.write(content)
        response.status_code = status_code
        for name, value in six.iteritems(headers):
            response.headers.append((name, value))
        return response

    def get_routes(self, path='', iden_format=r'(?P<iden>\w+)'):
        '''
        Prepare routes for the given REST resource

        :param path: string -- base path for the REST resource
        :param iden: string -- format for identifier, for instance might be
        used to make composite identifier
        '''
        return [
            url(
                r'^{}(?:\.(?P<data_format>\w+))?$'.format(path),
                self.wrap_request
            ),
            url(
                r'^{}/{}(?:\.(?P<data_format>\w+))?$'.format(
                    path, iden_format),
                self.wrap_request
            )
        ]
