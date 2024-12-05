from flask import Flask
from flask import jsonify
from flask_jwt_extended import JWTManager
from models import db
from routes import api

app = Flask(__name__)

# Security Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '#00001'



# Initialization
db.init_app(app)
jwt = JWTManager(app)



# Register blueprints
app.register_blueprint(api, url_prefix='/api')



# Create tables
with app.app_context():
    db.create_all()
    


# App routes
@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({"msg": "Welcome to the API!"}), 200



if __name__ == '__main__':
    app.run(debug=True)
