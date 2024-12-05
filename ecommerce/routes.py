from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from models import db, User, Product, Cart, CartProduct, Order, bcrypt
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import re

# API
api = Blueprint('api', __name__)


# Email Validation
def is_valid_email(email):
    email_regex = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

# Password validation
def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search('[A-Z]', password):  
        return False
    if not re.search('[a-z]', password):  
        return False
    if not re.search('[0-9]', password): 
        return False
    if not re.search('[!@#$%^&*(),.?":{}|<>]', password): 
        return False
    return True



# Authentication =======================================================================================================================

# Signup 
@api.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Email and password are required."}), 400

    if not is_valid_email(data['email']):
        return jsonify({"msg": "Invalid email format."}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already registered."}), 400
    
    if not is_valid_password(data['password']):
        return jsonify({"msg": "Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character."}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already registered."}), 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], email=data['email'], password=hashed_password, address=data.get('address'))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User  created successfully.", "user_id": new_user.id}), 201

# Signin
@api.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Invalid credentials."}), 401



#  Product Management ======================================================================================================================

#  Add Product
@api.route('/addproduct', methods=['POST'])
@jwt_required()
def add_product():
    data = request.get_json()
    if not data.get('name') or not data.get('price'):
        return jsonify({"msg": "Name and price are required."}), 400

    new_product = Product(name=data['name'], description=data['description'], price=data['price'], category=data['category'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"msg": "Product added successfully.", "product_id": new_product.id}), 201


#  Update Product
@api.route('/updateproduct/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    data = request.get_json()
    product = Product.query.get(product_id)
    if not product:
            return jsonify({"msg": "Product not found."}), 404

    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = data['price']
    if 'category' in data:
        product.category = data['category']

    db.session.commit()
    return jsonify({"msg": "Product updated successfully."}), 200


#  Delete Product
@api.route('/deleteproduct/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"msg": "Product not found."}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"msg": "Product deleted successfully."}), 200


#  Get All Products
@api.route('/products', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    if not products:
        return jsonify({"msg": "No products found."}), 404

    product_list = [{"id": p.id, "name": p.name, "description": p.description, "price": p.price, "category": p.category} for p in products]
    return jsonify(product_list), 200



#  Cart Management ============================================================================================================================================================

# Add Product to Cart
@api.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    data = request.get_json()
    user_id = get_jwt_identity()
    product_id = data.get('product_id')

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"msg": "Product not found."}), 404

    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

    if CartProduct.query.filter_by(cart_id=cart.id, product_id=product_id).first():
        return jsonify({"msg": "Product already in cart."}), 400

    cart_product = CartProduct(cart_id=cart.id, product_id=product_id)
    db.session.add(cart_product)
    db.session.commit()
    return jsonify({"msg": "Product added to cart successfully."}), 201


# Delete Product from Cart
@api.route('/cart/delete', methods=['DELETE'])
@jwt_required()
def delete_from_cart():
    data = request.get_json()
    user_id = get_jwt_identity()
    product_id = data.get('product_id')

    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({"msg": "Cart not found."}), 404

    cart_product = CartProduct.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if not cart_product:
        return jsonify({"msg": "Product not found in cart."}), 404

    db.session.delete(cart_product)
    db.session.commit()
    return jsonify({"msg": "Product removed from cart successfully."}), 200


#  Get Cart Products
@api.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({"msg": "Cart is empty."}), 404

    cart_products = CartProduct.query.filter_by(cart_id=cart.id).all()
    if not cart_products:
        return jsonify({"msg": "Cart is empty."}), 404

    cart_details = []
    total_amount = 0
    for cp in cart_products:
        product = Product.query.get(cp.product_id)
        cart_details.append({
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price
        })
        total_amount += product.price

    return jsonify({"cart": cart_details, "total_amount": total_amount}), 200



# Order Management ==============================================================================================================================================

# Place Order
@api.route('/placeorder', methods=['POST'])
@jwt_required()
def place_order():
    data = request.get_json()
    user_id = get_jwt_identity()
    shipping_details = data.get('shipping_details')

    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart or not cart.products:
        return jsonify({"msg": "Cart is empty."}), 400

    order = Order(user_id=user_id, shipping_details=shipping_details, order_date=datetime.utcnow())
    db.session.add(order)
    db.session.commit()

    db.session.delete(cart)
    db.session.commit()
    return jsonify({"msg": "Order placed successfully.", "order_id": order.id}), 201


# Get Orders
@api.route('/getorders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).all()
    
    if not orders:
        return jsonify({"msg": "No orders found."}), 404

    order_list = []
    for order in orders:
        order_details = {
            "order_id": order.id,
            "order_date": order.order_date,
            "shipping_details": order.shipping_details,
            "status": order.status,
            "items": []
        }
        
        cart_products = CartProduct.query.filter_by(cart_id=order.id).all()
        for cp in cart_products:
            product = Product.query.get(cp.product_id)
            order_details["items"].append({
                "product_id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price
            })
        
        order_list.append(order_details)

    return jsonify(order_list), 200
   
