from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, make_response
from app.users.models import Users, UsersSchema
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Resource, Api
import flask_restful
import jwt
from jwt import DecodeError, ExpiredSignature
from config import SECRET_KEY
from datetime import datetime, timedelta
from functools import wraps
from flask import g


users = Blueprint('users', __name__)
# http://marshmallow.readthedocs.org/en/latest/quickstart.html#declaring-schemas
schema = UsersSchema()


# JWT AUTh process start
def create_token(user):
    payload = {
        'sub': user.id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token.decode('unicode_escape')


def parse_token(req):
    token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, SECRET_KEY, algorithms='HS256')

# Login decorator function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.headers.get('Authorization'):
            response = jsonify(message='Missing authorization header')
            response.status_code = 401
            return response

        try:
            payload = parse_token(request)
        except DecodeError:
            response = jsonify(message='Token is invalid')
            response.status_code = 401
            return response
        except ExpiredSignature:
            response = jsonify(message='Token has expired')
            response.status_code = 401
            return response

        g.user_id = payload['sub']

        return f(*args, **kwargs)

    return decorated_function

# JWT AUTh process end

api = Api(users)


class Auth(Resource):

    def post(self):
        data = request.get_json(force=True)
        print(data)
        email = data['email']
        password = data['password']
        user = Users.query.filter_by(email=email).first()
        if user == None:
            response = make_response(
                jsonify({"message": "invalid username/password"}))
            response.status_code = 401
            return response
        if check_password_hash(user.password, password):

            token = create_token(user)
            return {'token': token}
        else:
            response = make_response(
                jsonify({"message": "invalid username/password"}))
            response.status_code = 401
            return response

api.add_resource(Auth, '/login')


# Adding the login decorator to the Resource class
class Resource(flask_restful.Resource):
    method_decorators = [login_required]


# Any API class now inheriting the Resource class will need Authentication
class User(Resource):

    def get(self):

        results = Users.query.all()
        users = schema.dump(results, many=True).data
        return jsonify({"users": users})


api.add_resource(User, '/users')
