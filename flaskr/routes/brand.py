import functools
import re
import os
from jsonschema import validate, draft7_format_checker
import jsonschema.exceptions
import json

from flask import (
    Blueprint, g, request, session, current_app, session
)

from passlib.hash import argon2
from sqlalchemy.exc import DBAPIError
from sqlalchemy import or_
from flaskr.db import session_scope
from flaskr.models.Brand import Brand
from flaskr.models.Cart import Cart, CartLine
from flaskr.models.User import User

from flaskr.email import send
from flaskr.routes.utils import login_required, not_login, cross_origin, is_logged_in
from datetime import date

bp = Blueprint('brands', __name__, url_prefix='/brands')

@bp.route("/getBrand", methods=['POST'])
def getBrand():

    # Load json data from json schema to variable request.json 'SCHEMA_FOLDER'
    schemas_direcotry = os.path.join(current_app.root_path, current_app.config['SCHEMA_FOLDER'])
    schema_filepath = os.path.join(schemas_direcotry, 'brand.schema.json')
    try:
        with open(schema_filepath) as schema_file:
            schema = json.loads(schema_file.read())
            validate(instance=request.json, schema=schema, format_checker=draft7_format_checker)

    except jsonschema.exceptions.ValidationError as validation_error:
        return {
            'code': 400,
            'message': validation_error.message
        }

    try:
        with session_scope() as db_session:

            brand = Brand(
                            name = request.json.get('name'),
                            description = request.json.get('description'),
                            logo = request.json.get('logo')
                )
            db_session.add(brand)

        return {
            'code': 200,
            'message': 'success'
        }, 200

    except DBAPIError as db_error:
        # Returns an error in case of a integrity constraint not being followed.
        return {
            'code': 400,
            'message': re.search('DETAIL: (.*)', db_error.args[0]).group(1)
        }, 400

@bp.route("/viewBrand", methods=['GET'])
def viewBrand():

    try:
        with session_scope() as db_session:

            queryProduct = db_session.query(Brand)

            totalbrand =[]

            for item in queryProduct:
                myitem = {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "logo": item.logo
                }
                totalbrand.append(myitem)
            totalbrand = {
                "allbrands": totalbrand
            }
            return totalbrand

        return {
            'code': 200,
            'message': 'success'
        }, 200

    except DBAPIError as db_error:
        # Returns an error in case of a integrity constraint not being followed.
        return {
            'code': 400,
            'message': re.search('DETAIL: (.*)', db_error.args[0]).group(1)
        }, 400

@bp.route("/delBrand", methods=["DELETE"])
def delBrand():
    # Load json data from json schema to variable request.json 'SCHEMA_FOLDER'
    schemas_direcotry = os.path.join(current_app.root_path, current_app.config['SCHEMA_FOLDER'])
    schema_filepath = os.path.join(schemas_direcotry, 'delbrand.schema.json')
    try:
        with open(schema_filepath) as schema_file:
            schema = json.loads(schema_file.read())
            validate(instance=request.json, schema=schema, format_checker=draft7_format_checker)

    except jsonschema.exceptions.ValidationError as validation_error:
        return {
            'code': 400,
            'message': validation_error.message
        }

    try:

        with session_scope() as db_session:

            queryProduct = db_session.query(Brand).filter(Brand.id == request.json.get("id")).one()

            db_session.delete(queryProduct)

            return {
                       'code': 200,
                       'message': 'success'
                   }, 200

    except DBAPIError as db_error:
        # Returns an error in case of a integrity constraint not being followed.
        return {
                   'code': 400,
                   'message': re.search('DETAIL: (.*)', db_error.args[0]).group(1)
               }, 400

@bp.route("/updateBrand", methods=["POST"])
def updateBrand():
    # Load json data from json schema to variable request.json 'SCHEMA_FOLDER'
    schemas_direcotry = os.path.join(current_app.root_path, current_app.config['SCHEMA_FOLDER'])
    schema_filepath = os.path.join(schemas_direcotry, 'updatebrand.schema.json')
    try:
        with open(schema_filepath) as schema_file:
            schema = json.loads(schema_file.read())
            validate(instance=request.json, schema=schema, format_checker=draft7_format_checker)

    except jsonschema.exceptions.ValidationError as validation_error:
        return {
            'code': 400,
            'message': validation_error.message
        }
    try:
        with session_scope() as db_session:

          brand_id = request.json.get("id")
          brand_name = request.json.get("name")
          brand_descriptipn = request.json.get("description")
          brand_logo = request.json.get("logo")
          queryProduct = db_session.query(Brand).filter(Brand.id == brand_id).one()

          if brand_name is not None:
              queryProduct.name = brand_name

          if brand_descriptipn is not None:
              queryProduct.description = brand_descriptipn

          if brand_logo is not None:
              queryProduct.logo = brand_logo

        return {
            'code': 200,
            'message': 'success'
        }, 200

    except DBAPIError as db_error:
        # Returns an error in case of a integrity constraint not being followed.
        return {
            'code': 400,
            'message': re.search('DETAIL: (.*)', db_error.args[0]).group(1)
        }, 400