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

from .models import CarSeries, db, Users, JWTTokenBlocklist, CarInfo, CarInfoDetail, object_as_dict
from .config import BaseConfig
import requests

from sqlalchemy.sql import func
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
car_info_detail = rest_api.model('CarInfoDetailModel', {"car_id": fields.String(required=True, min_length=1, max_length=32),
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
            return {"success": False, "msg": "无权限访问"}, 200

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
    


@rest_api.route('/api/cars/list')
class CarsSearch(Resource):
    def get(self):
        print("搜索", request.args)
        brand_name = request.args.get('brand_name', type=str)
        series_name = request.args.get('series_name', type=str)
        dealer_price = request.args.get('dealer_price', type=str)
        page = request.args.get('page', type=int, default=1)
        per_page = request.args.get('per_page', type=int, default=10)

        query = CarInfo.query
        if brand_name:
            print('搜索',brand_name)
            query = query.filter(CarInfo.brand_name.like(brand_name))
        if series_name:
            print('搜索',series_name)
            query = query.filter(CarInfo.series_name.like(series_name))
        if dealer_price:
            print('搜索',dealer_price)
            query = query.filter(CarInfo.dealer_price < dealer_price)

        total_items = query.count()
        print(total_items)
        query = query.offset((page - 1) * per_page).limit(per_page)
        cars = query.all()

        return create_success_response({
            'total': total_items,
            'list': [car.toDICT() for car in cars]
        })

@rest_api.route('/api/cars_series')
class CarsSearch(Resource):
    @token_required
    def get(self, user):
        print("搜索", request.args)
        series_id = request.args.get('series_id', type=str)
        brand_name = request.args.get('brand_name', type=str)
        outter_name = request.args.get('outter_name', type=str)
        dealer_price = request.args.get('dealer_price', type=str)
        page = request.args.get('page', type=int, default=1)
        per_page = request.args.get('per_page', type=int, default=10)

        query = CarSeries.query
        if series_id:
            query = query.filter(CarSeries.id == series_id)
        if brand_name:
            print('搜索',brand_name)
            query = query.filter(CarSeries.brand_name.like(brand_name))
        if outter_name:
            print('搜索',outter_name)
            query = query.filter(CarSeries.outter_name.like(outter_name))
        if dealer_price:
            print('搜索',dealer_price)
            query = query.filter(CarSeries.dealer_price < dealer_price)

        total_items = query.count()
        print(total_items)
        query = query.offset((page - 1) * per_page).limit(per_page)
        cars = query.all()

        return create_success_response({
            'total': total_items,
            'list': [car.toDICT() for car in cars]
        })


@rest_api.route('/api/cars/info/detail')
class CarsInfoDetailSearch(Resource):
    # @token_required
    # @rest_api.expect(car_info_detail)
    def get(self):
        print("搜索", request.args)
        car_id = request.args.get('car_id', type=str)

        sql = text("SELECT * FROM car_info_detail WHERE car_id = :car_id")
        result = db.session.execute(sql, params={"car_id": car_id})
        print(result)
        rows = result.fetchall()

        data = {}
        for row in rows:
            print(row)
            key = row.key
            value = row.value
            data[key] = value
         
        return create_success_response(data)
    

@rest_api.route('/api/cars/img')
class CarsInfoDetailSearch(Resource):
    # @token_required
    def get(self):
        print("搜索", request.args)
        name = request.args.get('name', type=str)
        car_id = request.args.get('car_id', type=str)

        sql = text("SELECT * FROM car_image_wg WHERE car_id = :car_id limit 10")
        if(name == 'gft'):
            sql = text("SELECT * FROM car_image_wg WHERE car_id = :car_id limit 10")
        if(name == 'ns'):
            sql = text("SELECT * FROM car_image_ns WHERE car_id = :car_id limit 10")
        if(name == 'kj'):
            sql = text("SELECT * FROM car_image_kj WHERE car_id = :car_id limit 10")

        print(sql)
        result = db.session.execute(sql, params={"car_id": car_id})
        rows = result.fetchall()
        list=[{"name": row.name, "car_id": row.car_id, "pic_url": row.pic_url} for row in rows]
         
        return create_success_response(list)