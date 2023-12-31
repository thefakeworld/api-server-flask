# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os, json

from flask import Flask, jsonify
from flask_cors import CORS

from .routes import rest_api
from .models import db

app = Flask(__name__)

from .routes2 import rest_api_blueprint

app.config.from_object('api.config.BaseConfig')

db.init_app(app)
rest_api.init_app(app)
app.register_blueprint(rest_api_blueprint)
CORS(app)

# Setup database
@app.before_first_request
def initialize_database():
    try:
        print('初始化数据库')
        db.create_all()
    except Exception as e:

        print('> Error: DBMS Exception: ' + str(e) )

        # fallback to SQLite
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')

        print('> Fallback to SQLite ')
        db.create_all()

"""
   Custom responses
"""

# 自定义404错误响应
@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=str(e)), 404

@app.after_request
def after_request(response):
    """
       Sends back a custom error with {"success", "msg"} format
    """
    if int(response.status_code) >= 400:
        print(''' 
              *********************
              拦截了
              *********************
              ''')
        response_data = json.loads(response.get_data())
        print(response_data)
        if "errors" in response_data:
            response_data = {"success": False,
                             "msg": list(response_data["errors"].items())[0][1]}
            response.set_data(json.dumps(response_data))
        response.headers.add('Content-Type', 'application/json')
    return response
