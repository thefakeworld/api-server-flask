from datetime import datetime
import secrets
from flask import jsonify, request
from sqlalchemy import desc
from flask_restx import Resource
from . import rest_api
from ..utills import create_success_response, secret_required, token_required, create_paginate_response
from ..models import db, SecretBlocklist

@rest_api.route('/secrets')
class SecretsResource(Resource):
    @rest_api.doc(responses={401: 'Unauthorized'}, security="apikey")
    # @token_required
    def post(self, current_user):

        # expire_at = data.get('expire_at')  # You may want to validate and parse the expiration date

        secret_key = secrets.token_hex(16)
        secret = SecretBlocklist(secret_key=secret_key, expiration_type=0)
        secret.save()
        return {'code': 0, 'data': secret_key, 'message': 'Secret added successfully'}, 201

    def put(self, secret_key):
        # Your logic for updating the secret
        return jsonify({'message': 'Secret updated successfully'})

    @token_required
    def get(self, current_user):
        secret_key = request.args.get('secret_key')
        page = request.args.get('page', type=int, default=1)
        per_page = request.args.get('pageSize', type=int, default=10)
        query = SecretBlocklist.query
        if(secret_key):
          query = query.filter(SecretBlocklist.secret_key == secret_key)

        secrets = query.order_by(desc(SecretBlocklist.created_at)).paginate(page=page, per_page=per_page)
        
        return create_paginate_response(secrets)



@rest_api.route('/secrets/batch')
class SecretsBatchResource(Resource):
    @rest_api.doc(responses={401: 'Unauthorized'}, security="apikey")
    # @token_required
    def post(self):
        req_data = request.get_json()
        # expire_at = data.get('expire_at')  # You may want to validate and parse the expiration date
        expiration_type = req_data.get('expiration_type')

        keys = []
        for _ in range(10009):
            new_key = secrets.token_hex(16)
            key_entry = SecretBlocklist(
                secret_key=new_key,
                created_at=datetime.now(),
                expiration_type=expiration_type
            )
            keys.append(new_key)
            db.session.add(key_entry)
        db.session.commit()
        
        return {'code': 0, 'data': len(keys), 'message': 'Secret added successfully'}, 201


@rest_api.route('/secret')
class SecretResource(Resource):
    @secret_required
    def get(secret):
        if not secret.active_date:
            secret.generate_expiration()
            secret.save()
        return create_success_response(secret.toDICT())
    # # 激活secret
    # def post(secret):
    #     secret.generate_expiration()
    #     return create_success_response(secret.toDICT())
    
