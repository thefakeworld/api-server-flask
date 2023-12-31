from datetime import datetime
from functools import wraps

from flask import request
import jwt
from .models import JWTTokenBlocklist, Users, db, SecretBlocklist
from .config import BaseConfig


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
            return {"success": False, "msg": "无权限访问"}, 401

        # data = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        # print('authorization', data)
        try:
            data = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
            print('authorization', data)
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


class SuccessResponse:
    def __init__(self, data, msg):
        self.code = 0
        self.data = data
        self.msg = msg

    def to_dict(self):
        return {"success": True, "msg": self.msg, "data": self.data, "code": self.code}

def create_success_response(data=None, msg='操作成功', status_code=200):
    
    try:
        success_response = SuccessResponse(data, msg)
        return success_response.to_dict(), status_code
    except Exception as e:
        # 如果发生异常，返回一个包含错误信息的 JSON 格式响应
        error_msg = f'Error creating success response: {str(e)}'
        return {'msg': error_msg, 'code': -1}, 500

def create_paginate_response(paginate):
    return create_success_response({
        'page': paginate.page,
        'pageSize': paginate.per_page,
        'total': paginate.total,
        'list': [item.toDICT() for item in paginate.items]
    })

# Usage example:
# user_json = {"_id": "123", "email": "example@example.com", "username": "example"}
# token = "abc123"

# success_response = create_success_response({"_id": user_json['_id'], "email": user_json['email'], "username": user_json['username'], "token": token})


"""
   Helper function for Secret key
"""

def secret_required(f):

    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get("X-SECRET-KEY")
        if not token:
            print('not token ', token)
            return {'msg': 'Secret key missing'}, 403

        secret = SecretBlocklist.query.filter_by(secret_key=token).first()

        if not secret:
            return {'msg': 'Invalid or expired secret key'}, 403

        if secret.expiration_type == '0':
            if secret.is_used:
                return {'msg': 'secret key 失效'}, 403
            elif secret.is_expired():
                secret.is_used = True
         
        if secret.is_expired():
            return {'msg': 'Invalid or expired secret key'}, 403
        else:
            return f(secret)

    return decorator

