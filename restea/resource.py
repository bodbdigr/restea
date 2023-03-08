from __future__ import unicode_literals

import collections

import six

import restea.errors as errors
import restea.formats as formats
import restea.fields as fields


class Resource(object):
    '''
    Resource class implements all the logic of mapping HTTP methods to
    methods and error handling
    '''

    #: maps HTTP methods to class methods
    method_map = {
        'get': ('list', 'show'),
        'post': 'create',
        'put': 'edit',
        'delete': 'delete',
        'options': 'describe',
    }

    def __init__(self, request, formatter):
        '''
        :param request: request wrapper object
        :type request: :class: `restea.apapters.base.BaseRequestWrapper`

        :param formatter: formatter object
        :type formatter: :class: `restea.formats.BaseFormatter`
        '''
        if not hasattr(self, 'fields'):
            self.fields = fields.FieldSet()

        self.request = request
        self.formatter = formatter
        self._response_headers = collections.OrderedDict()

    def _iden_required(self, method_name):
        '''
        Checks if given method requires iden

        :param method_name: name of method on a resrouce
        :type method_name: str
        :returns: boolean value of whatever iden is needed or not
        :rtype: bool
        '''
        return method_name not in ('list', 'create', 'describe')

    def _match_response_to_fields(self, dct):
        '''
        Filters output from rest method to return only fields matching
        self.fields
        :param dct: dict to be filtered
        :type dct: dict
        :returns: filtered dict, with no values out of self.fields
        :rtype: dict
        '''
        return {
            k: v for k, v in dct.items()
            if k in self.fields.field_names
        }

    def _match_resource_list_to_fields(self, lst):
        '''
        Filters 'list' output from rest method to return only fields matching
        self.fields
        :param lst: list to be filtered
        :type lst: list, tuple, set
        :returns: filtered list, with no values out of self.fields
        :rtype: generator
        '''
        return (self._match_response_to_fields(item) for item in lst)

    def _apply_decorators(self, method):
        '''
        Returns method decorated with decorators specified in self.decorators
        :param method: resource instance method from self.method_map
        :type method: function
        :returns: decorated method
        :rtype: function
        '''
        if not hasattr(self, 'decorators'):
            return method

        for decorator in reversed(self.decorators):
            method = decorator(method)

        return method

    def _get_method_name(self, has_iden):
        '''
        Return resource object based on the HTTP method

        :param has_iden: specifies if requested url has iden (i.e /res/ vs
        /res/1)
        :type has_iden: bool
        :raises errors.MethodNotAllowedError: if HTTP method is not supprted
        :returns: name of the resource method name
        :rtype: str
        '''
        method = self.request.method
        method = self.request.headers.get(
            'HTTP_X_HTTP_METHOD_OVERRIDE',
            method
        )

        try:
            method_name = self.method_map[method.lower()]
        except KeyError:
            raise errors.MethodNotAllowedError(
                'Method "{}" is not supported'.format(self.request.method)
            )

        if isinstance(method_name, tuple):
            method_name = method_name[has_iden]

        if not has_iden and self._iden_required(method_name):
            raise errors.BadRequestError(
                'Given method requires iden'
            )

        if has_iden and not self._iden_required(method_name):
            raise errors.BadRequestError(
                'Given method shouldn\'t have iden'
            )

        return method_name

    @property
    def _is_valid_formatter(self):
        '''
        Returns is self.formatter refers to a valid formatter class object
        :returns: whatever self.formatter is valid or not
        :rtype: bool
        '''
        return (
            isinstance(self.formatter, type) and
            issubclass(self.formatter, formats.BaseFormatter)
        )

    @property
    def _error_formatter(self):
        '''
        Formatter used in case of error, uses self.formatter with fallback to
        `restea.formats.DEFAULT_FORMATTER`

        :returns: formatter object
        :rtype: :class: `restea.formats.BaseFormatter`
        '''
        if self._is_valid_formatter:
            return self.formatter
        else:
            return formats.DEFAULT_FORMATTER

    def _get_method(self, method_name):
        '''
        Returns method based on a name

        :param method_name: name of the method
        :type method_name: str
        :raises errors.BadRequestError: method is not implemented for a given
        resource
        :returns: method of the REST resource object
        :rtype: function
        '''
        method_exists = hasattr(self, method_name)
        if not method_exists:
            msg = 'Method "{}" is not implemented for a given endpoint'
            raise errors.BadRequestError(
                msg.format(self.request.method)
            )
        return getattr(type(self), method_name)

    def _get_payload(self, method_name):
        '''
        Returns a validated and parsed payload data for request

        :param method_name: name of the method
        :type method_name: str
        :raises restea.errors.BadRequestError: unparseable data
        :raises restea.errors.BadRequestError: payload is not mappable
        :raises restea.errors.BadRequestError: validation of fields not passed
        :returns: validated data passed to resource
        :rtype: dict
        '''
        if not self.request.data:
            return {}

        try:
            payload_data = self.formatter.unserialize(self.request.data)
        except formats.LoadError:
            raise errors.BadRequestError(
                'Fail to load the data'
            )

        if not isinstance(payload_data, collections.Mapping):
            raise errors.BadRequestError(
                'Data should be key -> value structure'
            )

        try:
            return self.fields.validate(method_name, payload_data)
        except fields.FieldSet.Error as e:
            raise errors.BadRequestError(str(e))
        except fields.FieldSet.ConfigurationError as e:
            raise errors.ServerError(str(e))

    def prepare(self):
        pass

    def finish(self, response):
        return response

    def process(self, *args, **kwargs):
        '''
        Processes the payload and maps HTTP method to resource object methods
        and calls the method

        :raises restea.errors.BadRequestError: wrong self.formatter type
        :raises restea.errors.ServerError: Some unhandled exception in
        resource method implementation or formatter serialization error

        :returns: serialized data to be returned to client
        :rtype: str
        '''
        if not self._is_valid_formatter:
            raise errors.BadRequestError('Not recognizable format')

        method_name = self._get_method_name(has_iden=bool(args or kwargs))
        self.payload = self._get_payload(method_name)
        method = self._get_method(method_name)
        method = self._apply_decorators(method)

        if method_name == 'describe':
            self._add_available_methods_to_response_headers()
        self.prepare()
        response = method(self, *args, **kwargs)
        response = self.finish(response)

        try:
            return self.formatter.serialize(response)
        except formats.LoadError:
            raise errors.ServerError('Service can\'t respond with this format')

    def dispatch(self, *args, **kwargs):
        '''
        Dispatches the request and handles exception to return data, status, content type, and
        headers

        :returns: 4-element tuple: result, HTTP status code, content type, and headers
        :rtype: tuple
        '''
        try:
            return (
                self.process(*args, **kwargs),
                200,
                self.formatter.content_type,
                self._response_headers
            )
        except errors.RestError as e:
            err = e.info.copy()
            err['error'] = str(e)

            return (
                self._error_formatter.serialize(err),
                e.http_code,
                self._error_formatter.content_type,
                self._response_headers
            )

    def _add_available_methods_to_response_headers(self):
        methods_available = []
        for http_method, method_name in self._stream_http_method_and_restea_method():
            if hasattr(self, method_name):
                methods_available.append(http_method.upper())
        self.set_header('Allow', ','.join(set(methods_available)))

    @classmethod
    def _stream_http_method_and_restea_method(cls):
        for http_method, method_names in six.iteritems(cls.method_map):
            if isinstance(method_names, tuple):
                for method_name in method_names:
                    yield http_method, method_name
            else:
                yield http_method, method_names

    def set_header(self, name, value):
        '''
        Sets the given response header name and value.
        :param name: string -- header name
        :param value: string -- header value
        '''
        self._response_headers[name] = value

    def clear_header(self, name):
        '''
        Clears an outgoing header.
        :param name: string -- header name
        '''
        self._response_headers.pop(name, None)
