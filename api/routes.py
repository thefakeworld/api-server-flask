# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime, timezone, timedelta

from functools import wraps

from flask import json, jsonify, request
from flask_restx import Api, Resource, fields

import jwt

from api.utills import create_success_response

from .models import db, Users, JWTTokenBlocklist, CarInfo
from .config import BaseConfig
import requests

from sqlalchemy import text, inspect

rest_api = Api(version="1.0", title="Users API")


"""
    Flask-Restx models for api request and response data
"""

signup_model = rest_api.model('SignUpModel', {"username": fields.String(required=True, min_length=2, max_length=32),
                                              "email": fields.String(required=True, min_length=4, max_length=64),
                                              "password": fields.String(required=True, min_length=4, max_length=16)
                                              })

login_model = rest_api.model('LoginModel', {"email": fields.String(required=True, min_length=4, max_length=64),
                                            "password": fields.String(required=True, min_length=4, max_length=16)
                                            })

user_edit_model = rest_api.model('UserEditModel', {"userID": fields.String(required=True, min_length=1, max_length=32),
                                                   "username": fields.String(required=True, min_length=2, max_length=32),
                                                   "email": fields.String(required=True, min_length=4, max_length=64)
                                                   })


"""
   Helper function for JWT token required
"""

def token_required(f):

    @wraps(f)
    def decorator(*args, **kwargs):

        token = None

        if "authorization" in request.headers:
            token = request.headers["authorization"]

        if not token:
            return {"success": False, "msg": "Valid JWT token is missing"}, 400

        try:
            data = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
            current_user = Users.get_by_email(data["email"])

            if not current_user:
                return {"success": False,
                        "msg": "Sorry. Wrong auth token. This user does not exist."}, 400

            token_expired = db.session.query(JWTTokenBlocklist.id).filter_by(jwt_token=token).scalar()

            if token_expired is not None:
                return {"success": False, "msg": "Token revoked."}, 400

            if not current_user.check_jwt_auth_active():
                return {"success": False, "msg": "Token expired."}, 400

        except:
            return {"success": False, "msg": "Token is invalid"}, 400

        return f(current_user, *args, **kwargs)

    return decorator


"""
    Flask-Restx routes
"""


@rest_api.route('/api/users/register')
class Register(Resource):
    """
       Creates a new user by taking 'signup_model' input
    """

    @rest_api.expect(signup_model, validate=True)
    def post(self):

        req_data = request.get_json()

        _username = req_data.get("username")
        _email = req_data.get("email")
        _password = req_data.get("password")

        user_exists = Users.get_by_email(_email)
        if user_exists:
            return create_success_response(msg="Email already taken", status_code=400)

        new_user = Users(username=_username, email=_email)

        new_user.set_password(_password)
        new_user.save()

        return create_success_response({
            id: new_user.id,
        }, "The user was successfully registered")


@rest_api.route('/api/users/login')
class Login(Resource):
    """
       Login user by taking 'login_model' input and return JWT token
    """

    # @rest_api.expect(login_model, validate=True)
    def post(self):
        req_data = request.get_json()
        

        _email = req_data.get("email")
        _password = req_data.get("password")

        user_exists = Users.get_by_email(_email)
        print('登录', req_data)
        print('user_exists', user_exists)

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 400

        if not user_exists.check_password(_password):
            return {"success": False,
                    "msg": "Wrong credentials."}, 400

        # create access token uwing JWT
        token = jwt.encode({'email': _email, 'exp': datetime.utcnow() + timedelta(minutes=30)}, BaseConfig.SECRET_KEY)

        user_exists.set_jwt_auth_active(True)
        user_exists.save()

        return create_success_response({
            "token": token,
            "user": user_exists.toDICT()
        })


@rest_api.route('/api/users/edit')
class EditUser(Resource):
    """
       Edits User's username or password or both using 'user_edit_model' input
    """

    @rest_api.expect(user_edit_model)
    @token_required
    def post(self, current_user):

        req_data = request.get_json()

        _new_username = req_data.get("username")
        _new_email = req_data.get("email")

        if _new_username:
            self.update_username(_new_username)

        if _new_email:
            self.update_email(_new_email)

        self.save()

        return {"success": True}, 200

@rest_api.route('/api/users/get')
class SearchUser(Resource):
    """
       get_user using 'user_edit_model' input
    """
    @token_required
    def get(self, current_user):
        print("搜索", request.args)
        # req_data = request.get_json()

        # print('get_user', '获取用户信息', req_data)

        _id = request.args.get('id')
      
        user_exists = Users.get_by_id(_id)

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 400

        # # create access token uwing JWT
        # token = jwt.encode({'email': _email, 'exp': datetime.utcnow() + timedelta(minutes=30)}, BaseConfig.SECRET_KEY)

        # user_exists.set_jwt_auth_active(True)
        # user_exists.save()

        return create_success_response(user_exists.toDICT())


@rest_api.route('/api/users/logout')
class LogoutUser(Resource):
    """
       Logs out User using 'logout_model' input
    """

    @token_required
    def post(self, current_user):

        _jwt_token = request.headers["authorization"]

        jwt_block = JWTTokenBlocklist(jwt_token=_jwt_token, created_at=datetime.now(timezone.utc))
        jwt_block.save()

        self.set_jwt_auth_active(False)
        self.save()

        return {"success": True}, 200


@rest_api.route('/api/sessions/oauth/github/')
class GitHubLogin(Resource):
    def get(self):
        code = request.args.get('code')
        client_id = BaseConfig.GITHUB_CLIENT_ID
        client_secret = BaseConfig.GITHUB_CLIENT_SECRET
        root_url = 'https://github.com/login/oauth/access_token'

        params = { 'client_id': client_id, 'client_secret': client_secret, 'code': code }

        data = requests.post(root_url, params=params, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
        })

        response = data._content.decode('utf-8')
        access_token = response.split('&')[0].split('=')[1]

        user_data = requests.get('https://api.github.com/user', headers={
            "Authorization": "Bearer " + access_token
        }).json()
        
        user_exists = Users.get_by_username(user_data['login'])
        if user_exists:
            user = user_exists
        else:
            try:
                user = Users(username=user_data['login'], email=user_data['email'])
                user.save()
            except:
                user = Users(username=user_data['login'])
                user.save()
        
        user_json = user.toJSON()

        token = jwt.encode({"username": user_json['username'], 'exp': datetime.utcnow() + timedelta(minutes=30)}, BaseConfig.SECRET_KEY)
        user.set_jwt_auth_active(True)
        user.save()

        return {"success": True,
                "msg": '操作成功',
                "data": {
                    "_id": user_json['_id'],
                    "email": user_json['email'],
                    "username": user_json['username'],
                    "token": token,
                }}, 200
    


@rest_api.route('/api/cars/search')
class CarsSearch(Resource):
    def get(self):
        print("搜索", request.args)
        brand_name = request.args.get('brand_name', '')
        cars = CarInfo.query.filter(CarInfo.brand_name.like(brand_name)).limit(4).all()

        car_list = [car.toJSON() for car in cars]
        return car_list
        # return jsonify(car_list)
        car_fields = [field.name for field in inspect(CarInfo).columns]
        car_list = []
        for car in cars:
            car_dict = {
                'brand_id': car.brand_id,
                'brand_name': car.brand_name,
                'car_name': car.car_name,
                # 添加其他车辆信息的字段
            }
            car_list.append(car_dict)
        return jsonify(car_list, car_fields)
        
        # return json.dumps(cars)
        # ins = inspect(db.engine)  # 使用engine连接到数据库
        # columns = ins.get_columns("users")  # 获取数据库表的字段名
        # sql = text('SELECT * FROM users WHERE username = :name')
        # result = db.session.execute(sql, {'name': '熊明'}).fetchall()
        # import pandas  as pd
        # result = pd.read_sql(sql_statement, con=con)
        # data = result.to_dict(orient="records")

        # print(result)
        # engine = db.engine
        # connection = engine.connect()
        # cursor = connection.execute("select * from cars where brand='Toyota'")
        # cursor.close()
        # connection.close()

        return {"success": True, 
                # "res": result,
                # "res2": result2,
                # "cars": result,
                "msg": "搜索"}, 200
    