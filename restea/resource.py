import collections
import restea.errors as errors
import restea.formats as formats
import restea.fields as fields


# TODO: Add fileds with validation

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
    }

    def __init__(self, request, formatter):
        '''
        :param request: :class: `restea.apapters.base.BaseRequestWrapper`
        sublcass -- request wrapper object

        :param formatter: :class: `restea.formats.BaseFormatter` subclass --
        formatter class implementing serialization and unserialization of
        the data
        '''
        if not hasattr(self, 'fields'):
            self.fields = fields.FieldSet()

        self.request = request
        self.formatter = formatter

    def _iden_required(self, method_name):
        '''
        Checks if given method requires iden

        :param method_name: string -- name of method on a resrouce
        :returns: bool - boolean value of whatever iden is needed or not
        '''
        return method_name not in ('list', 'create')

    def _apply_decorators(self, method):
        '''
        Returns method decorated with decorators specified in self.decorators
        :param method: -- resource method
        :returns: decorated method
        '''
        if not hasattr(self, 'decorators'):
            return method

        for decorator in self.decorators:
            method = decorator(method)

        return method

    def _get_method_name(self, has_iden):
        '''
        Return resource object based on the HTTP method

        :param has_iden: specifies if requested url has iden (i.e /res/ vs
        /res/1)
        :raises errors.MethodNotAllowedError: if HTTP method is not supprted
        :returns: string - name of the resource method name
        '''
        method = self.request.method
        method = self.request.headers.get(
            'HTTP_X_HTTP_METHOD_OVERRIDE',
            method
        )
        method_name = self.method_map.get(method.lower())

        if not method_name:
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
        :returns: bool
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

        :returns: :class: subclass of `restea.formats.BaseFormatter`
        '''
        if self._is_valid_formatter:
            return self.formatter
        else:
            return formats.DEFAULT_FORMATTER

    def _get_method(self, method_name):
        '''
        Returns method based on a name

        :param method_name: string -- name of the method
        :raises errors.BadRequestError: method is not implemented for a given
        resource
        :returns: -- method of the REST resource object
        '''
        method_exists = hasattr(self, method_name)
        if not method_exists:
            msg = 'Method "{}" is not implemented for a given endpoint'
            raise errors.BadRequestError(
                msg.format(self.request.method)
            )
        return getattr(self, method_name)

    def _get_payload(self):
        '''
        Returns a validated and parsed payload data for request

        :raises restea.errors.BadRequestError: unparseable data
        :raises restea.errors.BadRequestError: payload is not mappable
        :raises restea.errors.BadRequestError: validation of fields not passed
        :returns: dict - validated data passed to resource
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
            return self.fields.validate(payload_data)
        except fields.FieldSet.Error, e:
            raise errors.BadRequestError(e.message)
        except fields.FieldSet.ConfigurationError, e:
            raise errors.ServerError(e.message)

    def process(self, *args, **kwargs):
        '''
        Processes the payload and maps HTTP method to resource object methods
        and calls the method

        :raises restea.errors.BadRequestError: wrong self.formatter type
        :raises restea.errors.ServerError: Some unhandled exception in
        resource method implementation or formatter serialization error

        :returns: string -- serialized data to be returned to client
        '''
        if not self._is_valid_formatter:
            raise errors.BadRequestError(
                'Not recognizeable format'
            )

        self.payload = self._get_payload()

        method_name = self._get_method_name(has_iden=bool(args or kwargs))
        method = self._get_method(method_name)
        method = self._apply_decorators(method)

        try:
            res = method(*args, **kwargs)
        except errors.RestError, e:
            raise e
        except Exception:
            raise errors.ServerError('Service is not available')

        try:
            return self.formatter.serialize(res)
        except formats.LoadError:
            raise errors.ServerError('Service can\'t respond with this format')

    def dispatch(self, *args, **kwargs):
        '''
        Dispatches the request and handles exception to return data, status
        and content type

        :returns: tuple -- 3 element tuple: result, HTTP status code and
        content type
        '''
        try:
            return (
                self.process(*args, **kwargs),
                200,
                self.formatter.content_type
            )
        except errors.RestError, e:
            err = {'error': e.message}
            if e.code:
                err.update({'code': e.code})

            return (
                self._error_formatter.serialize(err),
                e.http_code,
                self._error_formatter.content_type
            )
