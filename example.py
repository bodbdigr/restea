import random
from flask import Flask

from restpy import errors
from restpy.resource import Resource
from restpy.adapters.flaskwrap import FlaskResourceWrapper
from restpy import fields

app = Flask(__name__)

# Dummy data for the Resource
sites = [
    {
        'id': i,
        'name': 'my__site_{}'.format(i),
        'title': 'my site #{}'.format(i),
        'rating': random.randint(1, 5),
        'domain': 'www.my_domain_for_site_{}.com'.format(i),
        'anoher_field_out_of_scope': 'this one shouldn\'t be seen'
    } for i in xrange(1, 20)
]


def add_dummy_data(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if isinstance(res, dict):
            res['dummy_key'] = 'dummy value'
        return res
    return wrapper


class SiteResource(Resource):
    decorators = [add_dummy_data]

    fields = fields.FieldSet(
        id=fields.Integer(required=True),
        name=fields.String(max_length=50, required=True),
        title=fields.String(max_length=150)
    )

    def list(self):
        return sites

    def show(self, iden):
        try:
            return sites[int(iden)]
        except IndexError:
            raise errors.NotFoundError('Site doesn\'t exist', code=10)

    def edit(self, iden):
        return self.payload


with app.app_context():
    FlaskResourceWrapper(SiteResource).get_routes('/v1/sites')


if __name__ == '__main__':
    app.debug = True
    app.run()
