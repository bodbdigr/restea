import flask
import restea.formats as formats

from restea.adapters.base import (
    BaseResourceWrapper,
    BaseRequestWrapper,
)


class FlaskRequestWrapper(BaseRequestWrapper):
    '''
    Object wrapping Flask request context.
    '''
    @property
    def data(self):
        '''
        Returns a payload sent to server

        :returns: string -- raw value of payload sent to server
        '''
        return self._original_request.data.decode()

    @property
    def method(self):
        '''
        Returns HTTP method for the current request

        :returns: string -- HTTP method name
        '''
        return self._original_request.method

    @property
    def headers(self):
        '''
        Returns a headers dict

        :returns: dict -- received request headers
        '''
        return self._original_request.headers

    def get(self, value):
        '''
        Returns a value from the HTTP GET "map"

        :param value: string -- key from GET
        :returns: string -- value from GET or None if anything is found
        '''
        return self._original_request.values.get(value)


class FlaskResourceWrapper(BaseResourceWrapper):
    '''
    FlaskResourceWrapper implements Flask 'view' API for the
    `restea.Resource` object, aka routing and return values in Flask format
    '''
    @property
    def app(self):
        '''
        Returns current Flask application
        :returns: :class: `app.Flask` -- current Flask app
        '''
        return flask.current_app

    def wrap_request(self, *args, **kwargs):
        '''
        Prepares data and pass control to `restea.Resource` object

        :returns: :class: `flask.Response`
        '''
        data_format, kwargs = self._get_format_name(kwargs)
        formatter = formats.get_formatter(data_format)

        resource = self._resource_class(
            FlaskRequestWrapper(flask.request), formatter
        )
        res, status_code, content_type = resource.dispatch(*args, **kwargs)

        return flask.Response(
            res,
            mimetype=content_type,
            status=status_code
        )

    def __adapt_path(self, path):
        '''
        Adapts the path to path Flask requirements for the url routes

        :param path: string -- route path
        :returns: string -- normalized route path
        '''
        if not path.startswith('/'):
            return '/' + path
        return path

    def get_routes(self, path='', iden='<iden>'):
        '''
        Prepare routes for the given REST resource

        :param path: string -- base path for the REST resource
        :param iden: string -- format for identifier, for instance might be
        used to make composite identifier
        '''
        path = self.__adapt_path(path)
        routes = (
            '{}'.format(path),
            '{}/{}'.format(path, iden),
            '{}.<data_format>'.format(path),
            '{}/{}.<data_format>'.format(path, iden),
        )
        for route in routes:
            self.app.add_url_rule(
                route,
                view_func=self.wrap_request,
                methods=[m.upper() for m in self._resource_class.method_map]

            )
