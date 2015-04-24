import restea.formats as formats


class BaseResourceWrapper(object):
    '''
    BaseResourceWrapper is added to have common interface between frameworks.
    '''
    def __init__(self, resource_class):
        '''
        :param resource_class: :class: `restea.resource.Resource` -- resource
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
