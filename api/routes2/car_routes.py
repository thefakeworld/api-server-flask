from flask import request
from . import rest_api
from flask_restx import Resource
from ..utills import token_required, secret_required, create_success_response
from ..models import CarInfo, db, CarBrand
import requests
from sqlalchemy import text, inspect


@rest_api.route('/cars/brands')
class CarsBrands(Resource):
    def get(self):
        brandList = CarBrand.query.all()
        return create_success_response([car.toDICT() for car in brandList])

# @rest_api.route('/cars/data')
# class CarsData(Resource):
#     def get(self):
#         print("搜索", request.args)
#         car_id = request.args.get('car_id', type=str)
#         query = CarInfo.query.filter(CarInfo.car_id == car_id)
#         carData = query.first()
#         print('data', carData)
#         return create_success_response(carData.toJSON())

@rest_api.route('/cars/info/detail')
class CarsInfoDetailSearch(Resource):
    def get(self):
        print("搜索", request.args)
        car_id = request.args.get('car_id', type=str)

        sql = text("SELECT * FROM car_info_detail WHERE car_id = :car_id")
        result = db.session.execute(sql, params={"car_id": car_id})
        # print(result)
        rows = result.fetchall()

        data = {}
        for row in rows:
            # print(row)
            key = row.key
            value = row.value
            data[key] = value
         
        return create_success_response(data)
    

@rest_api.route('/cars/img')
class CarsInfoDetailSearch(Resource):
    @secret_required
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
    

@rest_api.route('/cars/img/dongche')
class CarsImageDongCheSearch(Resource):
    @secret_required
    def get(self):
        series_id = request.args.get('series_id', type=str)
        car_id = request.args.get('car_id', type=str)
        url = f"https://www.dongchedi.com/motor/pc/car/series/get_series_picture?aid=1839&app_name=auto_web_pc&series_id={series_id}&category=&offset=0&count=1&car_id={car_id}"
        headers = {
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Accept': '*/*',
            'Host': 'www.dongchedi.com',
            'Connection': 'keep-alive'
        }

        print('get dongche')
        response = requests.request("GET", url, headers=headers)

        try:
            dongcheJson = response.json()
            carList = dongcheJson['data']['picture_list']
            picurls = carList[0]['pic_url'] or []
            piclist = picurls[0: 10]
            return create_success_response(piclist)
        except:
            return create_success_response([], msg='没有图片')

