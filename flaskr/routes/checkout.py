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
from flaskr.models.Product import Product, Price, Order, OrderLine
from flaskr.models.Cart import Cart, CartLine
from flaskr.models.User import User

from flaskr.email import send
from flaskr.routes.utils import login_required, not_login, cross_origin, is_logged_in
from datetime import date

bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@bp.route("/getorder", methods =["POST"])
def getOrder():

    # Load json data from json schema to variable user_info.json 'SCHEMA_FOLDER'
    schemas_direcotry = os.path.join(current_app.root_path, current_app.config['SCHEMA_FOLDER'])
    schema_filepath = os.path.join(schemas_direcotry, 'user_info.schema.json')
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
        # Check if cart id exists with cart items
        with session_scope() as db_session:
            queryCart = db_session.query(Cart)
            queryCart = queryCart.filter(Cart.id == request.json.get('cart_id'))
            queryItem = db_session.query(CartLine)
            queryItem = queryItem.filter(CartLine.cart_id == request.json.get('cart_id'))
            
            total_price = 0
            
            for item in queryItem:
                cartID = item.cart_id
                productID = item.product_id
                quantity = item.quantity

                # Get product price
                queryPrice = db_session.query(Price).filter(Price.product_id == productID).one()
                productPrice = float(queryPrice.amount)

                # Create order line object
                #order_line = OrderLine(order_id = my_order.id, product_id = productID, 
                #                        quantity = quantity, price = productPrice)
                # Add to database
                #db_session.add(order_line)

                # Calculate total price
                total_price = total_price + productPrice*quantity


            # Get json data from json object
            user_id = queryCart.one().user_id
            #date_fulfilled = user_info.json.get('date_fulfilled')
            status_id = request.json.get('status_id')
            fullname = request.json.get('full_name')
            line1 = request.json.get('line1')
            line2 = request.json.get('line2')
            city = request.json.get('city')
            country = request.json.get('country')
            phone = request.json.get('phone')

            # Create order object
            my_order = Order(
                            user_id = user_id,
                            date_fulfilled = date.today(),
                            status_id = status_id,
                            full_name = fullname,
                            line1 = line1,
                            line2 = line2,
                            city = city,
                            country = country,
                            phone = phone,
                            total_cost = total_price,
                            promotion_code_id = 9
                            )
            # Add to database
            db_session.add(my_order)
            db_session.commit()

            for item in queryItem:
                cartID = item.cart_id
                productID = item.product_id
                quantity = item.quantity

                # Get product price
                queryPrice = db_session.query(Price).filter(Price.product_id == productID).one()
                productPrice = float(queryPrice.amount)

                # Create order line object
                order_line = OrderLine(order_id = my_order.id, product_id = productID, 
                                        quantity = quantity, cost = productPrice)
                # Add to database
                db_session.add(order_line)
                db_session.commit()


            # Prepare to clear cart
            # queryCart = db_session.query(Cart)
            # queryCart = queryCart.filter(Cart.id == request.json.get('cart_id')).one()
            queryItem = db_session.query(CartLine)
            queryItem = queryItem.filter(CartLine.cart_id == request.json.get('cart_id'))

            # CLEAR CART
            # db_session.delete(queryCart)
            db_session.delete(queryItem)


    except DBAPIError as db_error:
        # Returns an error in case of a integrity constraint not being followed.
        return {
            'code': 400,
            'message': 'error: ' + db_error.args[0]
        }, 400

@bp.route("/checkout", methods=['POST'])
def checkOut():

    # Load json data from json schema to variable request.json 'SCHEMA_FOLDER'
    schemas_direcotry = os.path.join(current_app.root_path, current_app.config['SCHEMA_FOLDER'])
    schema_filepath = os.path.join(schemas_direcotry, 'checkout.schema.json')
    try:
        with open(schema_filepath) as schema_file:
            schema = json.loads(schema_file.read())
            validate(instance=request.json, schema=schema, format_checker=draft7_format_checker)
            
    except jsonschema.exceptions.ValidationError as validation_error:
        return {
            'code': 400,
            'message': validation_error.message
        }

    stringList=""

    try:    

    # Check if cart id exists with cart items
        with session_scope() as db_session:
            queryCart = db_session.query(Cart)
            queryCart = queryCart.filter(Cart.id == request.json.get('cartID'))
            queryItem = db_session.query(CartLine)
            queryItem = queryItem.filter(CartLine.cart_id == request.json.get('cartID'))


            if queryCart.count() > 0 and queryItem.count() > 0:
                queryCart = queryCart.one()
                
                # Get buyer's ID from Cart
                userID = queryCart.user_id
            
                # Find buyer with user ID
                queryUser = db_session.query(User).filter(User.id == userID).one()
                
                # Get buyer's email
                emailBuyer = queryUser.email

                # iterate through list of items
                for item in queryItem:

                    # Get product by product ID
                    queryProduct = db_session.query(Product).filter(Product.id == item.product_id)

                    # Get Seller id
                    sellerID = queryProduct.one().user_id
                    
                    # Get seller ID by user ID
                    sellerQuery = db_session.query(User).filter(User.id == sellerID).one()
                    # Get seller email
                    emailSeller = sellerQuery.email
                    
                    # Get total quantity
                    total_quantity = int(queryProduct.one().quantity)
                    # Get quantity purchased
                    purchased_quantity = int(item.quantity)
                    # Get quantity left
                    left = total_quantity - purchased_quantity

                    # Get name of the product sold
                    productsold=str(queryProduct.one().name)
                    
                    # If quantity left is bigger than 0
                    if left >= 0:

                        # SEND EMAIL to seller
                        send(current_app.config['SMTP_USERNAME'], emailSeller, "Welcome to 354TheStars!", "<html><body><p>"+productsold+":"+str(purchased_quantity)+" SOLD </p></body></html>" ,"Welcome to 354TheStars!")

                        # Update list of products sold with quantity
                        stringList=stringList+"<p>"+ productsold + " has been purchased with quantity " + str(purchased_quantity) + "</p>"

                        # UPDATE QUANTITY in product table
                        queryProduct = queryProduct.one()
                        queryProduct.quantity = left
                        db_session.merge(queryProduct)
                        db_session.flush()
                        db_session.commit()
                        
                    elif left < 0:
                        return {
                            'code': 400,
                            'message': 'Quantity for product '+productsold+' is not sufficient to sell'
                        }, 400

                # SEND EMAIL to the buyer
                send(current_app.config['SMTP_USERNAME'], emailBuyer, "Welcome to 354TheStars!", "<html><body><p>Check out!</p>"+stringList+"</body></html>" ,"Welcome to 354TheStars!")

                
            else:
                return {
                    'error': 'Cart or Cartline not existed'
                }, 200
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

    

