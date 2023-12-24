from flask import Blueprint
from flask_restx import Api

rest_api_blueprint = Blueprint('api', __name__, url_prefix='/api')
rest_api = Api(rest_api_blueprint, version="1.0", title="Cars API", doc='/doc/v2')

# Import routes from other files
from . import car_routes
from . import secret_routes
