from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/super_simple")
def super_simple():
    return jsonify(message = "Hello from the planetary API")
    

@app.route('/error')
def return_error():
    return jsonify(message = "That resource was not found"), 404

@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))

    if age < 18:
        return jsonify(message = "Sorry " + name + ", you are not old enough"), 401
    else:
        return jsonify(message = "Welcome, " + name)


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 18:
        return jsonify(message = "Sorry " + name + ", you are not old enough"), 401
    else:
        return jsonify(message = "Welcome, " + name)


if __name__ == '__main__':
    app.run()