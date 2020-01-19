import os
from flask import Flask, request, jsonify, abort, redirect, url_for
from sqlalchemy import exc
import json
from flask_cors import CORS

from database.models import db_drop_and_create_all, setup_db, Drink
from auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()


@app.route('/')
def index():
    return redirect(url_for('drinks'))


@app.route('/drinks', methods=['GET'])
def drinks():
    """
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks or
        appropriate status code indicating reason for failure
    """
    drink_data = Drink.query.all()
    if not drink_data:
        abort(404)
    drinks_list = [drink.short() for drink in drink_data]
    result = {
        "success": True,
        "drinks": drinks_list
    }
    return jsonify(result)


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_detail(jwt):
    """
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    """
    drink_data = Drink.query.all()
    if not drink_data:
        abort(404)
    drinks_list = [drink.long() for drink in drink_data]
    result = {
        "success": True,
        "drinks": drinks_list
    }
    return jsonify(result)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    """
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
    """
    input_data = request.get_json()
    title = input_data.get('title', None)
    recipe = input_data.get('recipe', None)
    if not title or not recipe:
        abort(422)
    new_drink = Drink(title=title, recipe=json.dumps(recipe))
    try:
        new_drink.insert()
    except Exception as e:
        print(str(e))
        abort(422)
    result = {
        "success": True,
        "drinks": new_drink.long()
    }
    return jsonify(result)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(*args, **kwargs):
    """
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
    """
    drink_id = kwargs['id']
    target_drink = Drink.query.get(drink_id)
    input_data = request.get_json()
    title = input_data.get('title', None)
    recipe = input_data.get('recipe', None)
    if not target_drink:
        abort(404)
    if title:
        target_drink.title = title
    if recipe:
        target_drink.recipe = json.dumps(recipe)
    try:
        target_drink.insert()
    except Exception as e:
        print('EXCEPTION: ', str(e))
        abort(400)
    result = {
        "success": True,
        "drinks": [target_drink.long()]
    }
    return jsonify(result)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(*args, **kwargs):
    """
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
        returns status code 200 and json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
    """
    drink_id = kwargs['id']
    target_drink = Drink.query.get(drink_id)
    if not target_drink:
        abort(404)
    try:
        target_drink.delete()
    except Exception as e:
        print('EXCEPTION: ', str(e))
        abort(500)
    result = {
        "success": True,
        "delete": drink_id
    }
    return jsonify(result)


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    result = {
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }
    return jsonify(result), 422


@app.errorhandler(404)
def not_found(error):
    result = {
        "success": False,
        "error": 404,
        "message": "resource not found"
    }
    return jsonify(result), 404


@app.errorhandler(400)
def bad_request(error):
    result = {
        "success": False,
        "error": 400,
        "message": "bad request"
    }
    return jsonify(result), 400


@app.errorhandler(500)
def server_error(error):
    result = {
        "success": False,
        "error": 500,
        "message": "server error"
    }
    return jsonify(result), 500


@app.errorhandler(AuthError)
def auth_error(error):
    response = jsonify(error.error)
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    app.run()
