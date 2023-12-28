# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime, timedelta

import json
import pymysql

from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy, inspect

# database
pymysql.install_as_MySQLdb()
db = SQLAlchemy()

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

class Users(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.Text())
    jwt_auth_active = db.Column(db.Boolean())
    date_joined = db.Column(db.DateTime(), default=datetime.now)

    def __repr__(self):
        return f"User {self.username}"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def update_email(self, new_email):
        self.email = new_email

    def update_username(self, new_username):
        self.username = new_username

    def check_jwt_auth_active(self):
        return self.jwt_auth_active

    def set_jwt_auth_active(self, set_status):
        self.jwt_auth_active = set_status

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def toDICT(self):

        cls_dict = {}
        cls_dict['_id'] = self.id
        cls_dict['username'] = self.username
        cls_dict['email'] = self.email

        return cls_dict

    def toJSON(self):

        return self.toDICT()


class JWTTokenBlocklist(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    jwt_token = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return f"Expired Token: {self.jwt_token}"
    
    def save(self):
        db.session.add(self)
        db.session.commit()


class SecretBlocklist(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    secret_key = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    expire_at = db.Column(db.DateTime(), nullable=False, default=datetime.now() + timedelta(weeks=1))

    def __repr__(self):
        return f"Expired Secret: {self.secret_key}"
    
    def toDICT(self):
        cls_dict = {}
        cls_dict['id'] = self.id
        cls_dict['secret_key'] = self.secret_key
        cls_dict['created_at'] = self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        cls_dict['expire_at'] = self.expire_at.strftime('%Y-%m-%d %H:%M:%S')
        return cls_dict

    def save(self):
        print('保持', self)
        db.session.add(self)
        db.session.commit()

class CarBrand(db.Model):
    
    brand_name = db.Column(db.String(50))
    brand_id = db.Column(db.String(50), primary_key=True)
    pinyin = db.Column(db.String(50))
    image_url = db.Column(db.String(120))
    def toDICT(self):
        return object_as_dict(self)

    def toJSON(self):
        return self.toDICT()

class CarInfo(db.Model):
    
    car_name = db.Column(db.String(50))
    dealer_text = db.Column(db.String(50))
    series_type = db.Column(db.String(50))
    series_name = db.Column(db.String(50))
    official_price = db.Column(db.String(10))
    series_id = db.Column(db.String(50))
    dealer_price = db.Column(db.String(50))
    has_dealer_price = db.Column(db.Boolean)
    sale_status = db.Column(db.Integer)
    car_page_enable = db.Column(db.Boolean)
    car_year = db.Column(db.String(50))
    brand_name = db.Column(db.String(50))
    brand_id = db.Column(db.String(50))
    car_id = db.Column(db.String(50), primary_key=True)

    def toDICT(self):
        return object_as_dict(self)

    def toJSON(self):

        return self.toDICT()
    

class CarSeries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cover_url = db.Column(db.String(50))
    brand_name = db.Column(db.String(50))
    outter_name = db.Column(db.String(50))
    brand_id = db.Column(db.String(50))
    dealer_price = db.Column(db.String(50))
    has_dealer_price = db.Column(db.Boolean)
    official_price = db.Column(db.String(10))
    has_official_price = db.Column(db.Boolean)

    def toDICT(self):
        return object_as_dict(self)

    def toJSON(self):

        return self.toDICT()
    

class CarInfoDetail(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    car_id = db.Column(db.String(50))
    series_id = db.Column(db.String(50))
    key = db.Column(db.String(50))
    value = db.Column(db.String(50))
    def toDICT(self):
        return object_as_dict(self)

    def toJSON(self):
        return self.toDICT()


# class CarImageWg(db.Model):
#     car_id = db.Column(db.Integer())
#     series_id = db.Column(db.Integer())
#     pic_url = db.Column(db.String(150))
#     large_pic_url = db.Column(db.String(150))
#     name = db.Column(db.String(50))
#     def toDICT(self):
#         return object_as_dict(self)

#     def toJSON(self):
#         return self.toDICT()
    
#  继续改写 https://www.orcode.com/question/440549_ke84c5.html
# rows = conn.execute(query)
# list_of_dicts = [{key: value for (key, value) in row.items()} for row in rows]