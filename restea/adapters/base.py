import restea.formats as formats


class BaseResourceWrapper(object):
    '''
    BaseResourceWrapper is added to have common interface between frameworks.
    '''
    request_wrapper_class = None

    def __init__(self, resource_class):
        '''
        :param resource_class: :class:`restea.resource.Resource` -- resource
        object implementing methods to create/edit/delete data
        '''
        self._resource_class = resource_class

    def _get_format_name(self, view_kwargs):
        '''
        Returns format for serialization and unserialization of data

        :param view_kwargs: dict -- kwargs of the view catched from the
        url router

        :returns: tuple -- data_format found and modified kwargs
        '''
        data_format = view_kwargs.pop('data_format', None)
        if not data_format:
            data_format = formats.DEFAULT_FORMATTER.name
        return data_format, view_kwargs

    def get_routes(self, path='', iden=''):
        '''
        Prepare routes for the given REST resource

        :param path: string -- base path for the REST resource
        :param iden: string -- format for identifier, for instance might be
        used to make composite identifier
        '''
        raise NotImplementedError

    def prepare_response(self, content, status_code, content_type, headers):
        '''
        Prepares response for the given arguments.

        :param content: string -- response content
        :param status_code: string -- response status code
        :param content_type: string -- response content type
        :param headers: string -- response headers
        '''
        raise NotImplementedError

    def split_request_and_arguments(self, *args, **kwargs):
        '''
        Hook to return the original request object and arguments.

        This method receives all arguments that the `wrap_request` method
        receives and return the first argument as the request object by
        default which is commonly received in that order.
        Override this method in your subclass wrapper if the behavior is
        different for your framework.
        '''
        return args[0], args[1:], kwargs

    def wrap_request(self, *args, **kwargs):
        '''
        Prepares data and pass control to `restea.Resource` object
        :returns: Response object for corresponding framework
        '''
        data_format, kwargs = self._get_format_name(kwargs)
        formatter = formats.get_formatter(data_format)
        original_request, args, kwargs = self.split_request_and_arguments(
            *args, **kwargs
        )

        if not self.request_wrapper_class:
            raise RuntimeError(
                '{} must have a request_wrapper_class attribute '
                'configured.'.format(self.__class__.__name__)
            )

        resource = self._resource_class(
            self.request_wrapper_class(original_request), formatter
        )
        response_tuple = resource.dispatch(*args, **kwargs)

        if len(response_tuple) == 3:
            # For backward compatibility, it adds an empty dict as headers
            response_tuple += ({},)

        return self.prepare_response(*response_tuple)


class BaseRequestWrapper(object):
    '''
    BaseRequestWrapper wraps the `restea.request.Request` objects to abstract
    implementation between different frameworks
    '''
    def __init__(self, original_request):
        '''
        :param original_request: -- request object from the given framework
        '''
        self._original_request = original_request

    @property
    def data(self):
        '''
        Returns a payload sent to server

        :returns: string -- raw value of payload sent to server
        '''
        raise NotImplementedError

    @property
    def headers(self):
        '''
        Returns a headers dict

        :returns: dict -- received request headers
        '''
        raise NotImplementedError

    @property
    def method(self):
        '''
        Returns HTTP method for the current request

        :returns: string -- HTTP method name
        '''
        raise NotImplementedError

    def get(self, value):
        '''
        Returns a value from the HTTP GET "map"

        :param value: string -- key from GET
        :returns: string -- value from GET or None if anything is found
        '''
        raise NotImplementedError
