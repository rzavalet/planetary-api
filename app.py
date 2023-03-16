from flask import Flask, jsonify

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


if __name__ == '__main__':
    app.run()