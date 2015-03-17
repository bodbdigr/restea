import random
from flask import Flask

from restpy import errors
from restpy.resource import Resource
from restpy.adapters.flaskwrap import FlaskResourceWrapper


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


class SiteResource(Resource):
    # TODO: To be implemented
    #decorators = [session_required]

    #fields = dict(
    #    id=fields.Integer(required=True),
    #    name=fields.String(max_length=50, required=True),
    #    title=fields.String(max_length=150, default='title'),
    #    rating=fields.Integer(range=(1,5)),
    #    domain=fields.WebAddress(with_path=False),
    #)

    def list(self):
        return sites

    def show(self, iden):
        try:
            return sites[int(iden)]
        except IndexError:
            raise errors.NotFoundError('Site doesn\'t exist', code=10)

    def edit(self, iden):
        return {'name': self.payload.get('name')}


with app.app_context():
    FlaskResourceWrapper(SiteResource).get_routes('/v1/sites')


if __name__ == '__main__':
    app.debug = True
    app.run()
