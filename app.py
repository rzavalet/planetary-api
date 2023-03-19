'''
A simple Rest API server to show how to build one using Flask and Flask related modules.
'''

import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

basedir = os.path.abspath(os.path.dirname(__file__))


#-------------------------------------------------------
# Initialize the Flask application
#-------------------------------------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'insecure-secret'
app.config['MAIL_SERVER']= os.environ['MAIL_SERVER']
app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']


#-------------------------------------------------------
# Create objects of these types based on the Flask app
#-------------------------------------------------------
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwq = JWTManager(app)
mail = Mail(app)


#-------------------------------------------------------
# Some Flask CLI commands to initialize the SQLite DB
#-------------------------------------------------------
@app.cli.command('db_create')
def db_create():
    """
    Create the backend database
    """
    db.create_all()
    print("Done creating database")


@app.cli.command('db_drop')
def db_drop():
    """
    Drop the backend database
    """
    db.drop_all()
    print("Done dropping database")


@app.cli.command('db_seed')
def db_seed():
    """
    Add a few registers to the backedn database
    """
    mercury = Planet(planet_name = "Mercury",
                        planet_type = 'Class D',
                        home_star = 'Sun',
                        mass = 3.258e23,
                        radius = 1516,
                        distance = 35.98e6)

    venus = Planet(planet_name = "Venus",
                        planet_type = 'Class K',
                        home_star = 'Sun',
                        mass = 4.867e24,
                        radius = 3760,
                        distance = 67.24e6)

    earth = Planet(planet_name = "Earth",
                        planet_type = 'Class M',
                        home_star = 'Sun',
                        mass = 5.972e24,
                        radius = 3959,
                        distance = 92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)


    test_user = User(first_name = 'William',
                    last_name = 'Hershel',
                    email = 'test@test.com',
                    password = '123456')
    db.session.add(test_user)

    db.session.commit()

    print("Done seeding database")




#-------------------------------------------------------
# Here are the Flask route for our API
#-------------------------------------------------------
@app.route("/")
def hello_world():
    """
    The default API route
    """
    return "<p>Hello, World!</p>"


@app.route("/super_simple")
def super_simple():
    """
    Demonstrate json response
    """
    return jsonify(message = "Hello from the planetary API")


@app.route('/error')
def return_error():
    """
    Demonstrate how to return a 404 HTTP code
    """
    return jsonify(message = "That resource was not found"), 404


@app.route('/parameters')
def parameters():
    """
    Show how to take parameters in an API
    """
    name = request.args.get('name')
    age = int(request.args.get('age'))

    if age < 18:
        return jsonify(message = "Sorry " + name + ", you are not old enough"), 401
    else:
        return jsonify(message = "Welcome, " + name)


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    """
    Show how to take parameters from the URL string
    """
    if age < 18:
        return jsonify(message = "Sorry " + name + ", you are not old enough"), 401
    else:
        return jsonify(message = "Welcome, " + name)


@app.route('/planets', methods=['GET'])
def planets():
    """
    Endpoint to show all planets in our service
    """
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    """
    Endpoint to register a new user in our service
    """
    email = request.form['email']
    test = User.query.filter_by(email = email).first()
    if test:
        return jsonify(message = 'That email already exists'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name = first_name,
                    last_name = last_name,
                    password = password,
                    email = email)
        db.session.add(user)
        db.session.commit()
        return jsonify(message = "User created successfully"), 201


@app.route('/login', methods=['POST'])
def login():
    """
    Endpoint to log in a user
    """
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    
    test = User.query.filter_by(email = email, password = password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded", access_token=access_token)
    else:
        return jsonify(message='You entered a bad email or password'), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email:str):
    """
    Endpoint to recover a user's password via email
    """
    user = User.query.filter_by(email=email).first()
    if user:
        msg=Message(subject='Here is your planetary API password', 
                    sender='admin@planetary.api.com', 
                    recipients=[email],
                    body=f'Your planetary API password is {user.password}'
                    )
        mail.send(msg)
        return jsonify(message=f'Password sent to {email}')
    else:
        return jsonify(message='That email does not exist'), 401


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def plannet_details(planet_id: int):
    """
    Endpoint to retrieve only one planet
    """
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message='That planet does not exist'), 404


@app.route('/add_planet', methods=['POST'])
@jwt_required()
def add_planet():
    """
    Endpoint to add a new planet
    """
    planet_name = request.json['planet_name']

    planet = Planet.query.filter_by(planet_name=planet_name).first()
    if planet:
        return jsonify(f'There is already a planet {planet_name}'), 409

    planet_type = request.json['planet_type']
    home_star = request.json['home_star']
    mass = float(request.json['mass'])
    radius = float(request.json['radius'])
    distance = float(request.json['distance'])

    new_planet = Planet(planet_name = planet_name,
                        planet_type = planet_type,
                        home_star = home_star,
                        mass = mass,
                        radius = radius,
                        distance = distance)

    db.session.add(new_planet)
    db.session.commit()

    return jsonify(f'Successfully added planet {planet_name}'), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required()
def update_planet():
    """
    Endpoint to update the values of a planet
    """
    planet_name = request.json['planet_name']

    planet = Planet.query.filter_by(planet_name=planet_name).first()
    if planet:
        planet_type = request.json['planet_type']
        home_star = request.json['home_star']
        mass = float(request.json['mass'])
        radius = float(request.json['radius'])
        distance = float(request.json['distance'])

        planet.planet_type = planet_type
        planet.home_star = home_star
        planet.mass = mass
        planet.radius = radius
        planet.distance = distance

        db.session.commit()

        return jsonify(f'Successfully updated planet {planet_name}'), 202

    else:
        return jsonify(f'There is not planet {planet_name} in my records'), 404


@app.route('/delete_planet/<string:planet_name>', methods=['DELETE'])
@jwt_required()
def delete_planet(planet_name:str):
    """
    Endpoint to delete a planet from the backend
    """

    planet = Planet.query.filter_by(planet_name=planet_name).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()

        return jsonify(f'Successfully deleted planet'), 202

    else:
        return jsonify(f'There is no planet {planet_name} in my records'), 404



#-------------------------------------------------------
# Here are the DB Models for our API
#-------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)



#-------------------------------------------------------
# Here are the ORM Schemas for our API
#-------------------------------------------------------
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id',
                  'first_name',
                  'last_name',
                  'email',
                  'password')

class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id',
                  'planet_name',
                  'planet_type',
                  'home_star',
                  'mass', 'radius',
                  'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


#-------------------------------------------------------
# The flask application is run here
#-------------------------------------------------------
if __name__ == '__main__':
    app.run()