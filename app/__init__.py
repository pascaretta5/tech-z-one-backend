from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate
from products.enum import ProductsType
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config.from_object('config')
jwt = JWTManager(app)
db = SQLAlchemy(app)
users = []
products = []
selected_products = []

#PRODUCT Class
class Products(db.Model) : 
    id = db.Column(db.Integer, primary_key = True)
    type = db.Column(db.Enum(ProductsType), nullable = False, default = ProductsType.Others)
    item = db.Column(db.String(100), nullable = False)
    description = db.Column(db.String(1000), nullable = False)
    price = db.Column(db.Numeric(precision=10, scale=2), nullable = False)

#USER Class
class User(db.Model) :
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(100), nullable = False)
    basket = db.relationship('Basket', backref = 'user', lazy = True)

#BASKET Class
class Basket(db.Model) :
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    product = db.relationship('Products', secondary = 'products_basket', backref = db.backref('basket', lazy = True))

products_basket = db.Table('products_basket', 
                           db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key = True),
                           db.Column('basket_id', db.Integer, db.ForeignKey('basket.id'), primary_key = True),                         
                           )    
    
       
class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2))
    email = fields.Email(required=True)
    #verificar se o max vai ter erro
    password = fields.Str(required=True, validate=validate.Length(min=6, max=20))    

#Stuck trying to import from routes, so pasting in init
@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_me():
    actual_user = get_jwt_identity()
    return jsonify(actual_user)

#LIST users
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_all_users():
    list_user = User.query.all()
    users_json = [{ 'id' : user.id, 'name' : user.name, 'email' : user.email} for user in list_user]
    return jsonify({ 'users' : users_json })

#CREATE user
@app.route('/api/register', methods=['POST'])
def create_user():
    user_data = request.json
    print(user_data)
    #Validation
    errors = UserSchema().validate(user_data)
    if errors:
        return jsonify({'error': errors}), 400
    temp_user = User.query.filter(User.email == user_data['email']).first()

    if temp_user is not None:
        return jsonify({'error': "Email already registered"}), 400
      
        
    new_user = User(name = user_data['name'], email = user_data['email'], password = user_data['password'])
    db.session.add(new_user)
    db.session.commit()
    created_user = { 'id' : new_user.id, 'name' : new_user.name, 'email' : new_user.email}
    return jsonify(created_user), 201
    

#UPDATE user    
@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    user = User.query.get(user_id)
    if user is not None :
        user_data = request.json
        errors = UserSchema().validate(user_data)
        if errors:
            return jsonify({'error': errors}), 400
        user.name = user_data['name']
        user.email = user_data['email']
        user.password = user_data['password']
        db.session.commit()
        updated_user = { 'id' : user.id, 'name' :user.name, 'email': user.email}
        return jsonify(updated_user), 201    
    else :
        return jsonify({'message':'User not found'}), 404
    
#DELETE user
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get(user_id)
    if user is not None :
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message':'User successfully deleted'}), 201
    else :
        return jsonify({'message': 'User not found'}), 404
         
#Get user by ID
@app.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    if user is not None :
        found_user = { 'id' : user.id, 'name' : user.name, 'email' : user.email}
        return jsonify({'user' : found_user})
    else :
        return jsonify({'message' : 'User not found'}), 404

#LIST products
@app.route('/api/products', methods=['GET'])
def get_all_products():
    list_products = Products.query.all()
    products_json = [{ 'id' : products.id, 'type' : products.type.value, 'item' : products.item, 'description' : products.description, 'price' : products.price} for products in list_products]
    return jsonify({ 'products' : products_json })

#CREATE product
@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    product_data = request.json
    new_product = Products(type = product_data['type'], item = product_data['item'], description = product_data['description'], price = product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    created_product = {'type' : new_product.type.value, 'item' : new_product.item, 'description' : new_product.description, 'price' : new_product.price}
    return jsonify(created_product), 201

#UPDATE product
@app.route('/api/products/<int:products_id>', methods=['PUT'])
@jwt_required()
def update_product(products_id):
    products = Products.query.get(products_id)
    if products is not None :
        product_data = request.json
        products.type = product_data['type']
        products.item = product_data['item']
        products.description = product_data['description']
        products.price = product_data['price']
        db.session.commit()
        updated_product = {'id' :products.id, 'type' : products.type.value, 'item' : products.item,'description' : products.description, 'price' : products.price}
        return jsonify(updated_product), 201
    else :
        return jsonify({'message' : 'Product not found'}), 404
    
#DELETE product
@app.route('/api/products/<int:products_id>', methods=['DELETE'])
@jwt_required()
def delete_product(products_id):
    products = Products.query.get(products_id)
    if products is not None :
        db.session.delete(products)
        db.session.commit()
        return jsonify({'message' : 'Product deleted successfully'}), 200
    else :
        return jsonify({'message' : ' Product not found'})
    
#LOGIN    
@app.route('/api/login', methods=['POST'])
def login():
    login_data = request.json
    user = User.query.filter_by(email = login_data['email']).first()
    if user and verify_password(user.password, login_data['password']) :
        access_token = create_access_token(identity=user.id)
        return jsonify({'token' : access_token}), 200   
    else :
        return jsonify({'message' : 'Invalid credentials'}), 401

def verify_password(user_password, login_password):
    if user_password == login_password :
        return True
    else :
        return False
        
#List basket route
@app.route('/api/vending', methods=['GET'])
@jwt_required()
def vending():
    my_id = get_jwt_identity()
    shop = Basket.query.filter_by(user_id = my_id).all()
    shop_json = [
        {
            'id' : basket.id, 
            'date' : basket.date.isoformat(),
            'products' : [
                {
                    'id' : product.id,
                    'item' : product.item
                } for product in basket.product
            ]
        } for basket in shop
    ]
    return jsonify({'shop' : shop_json}), 200

#Add to BASKET
@app.route('/api/vending', methods=['POST'])
@jwt_required()
def buying():
    my_id = get_jwt_identity()
    list_products = request.json
    new_basket = Basket( user_id = my_id)
    products_ids = list_products['products_ids']
    products = Products.query.filter(Products.id.in_(products_ids)).all()
    new_basket.product.extend(products)
    db.session.add(new_basket)
    db.session.commit()
    return jsonify({'message' : 'Successfully added to basket'}), 201
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()