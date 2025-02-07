import flask
import waitress














def run():
    app = flask.Flask(__name__)
    app.config['SECRET_KEY'] = 'supe