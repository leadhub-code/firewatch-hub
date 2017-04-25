import flask

from .views import bp as views_bp


def get_app():
    app = flask.Flask(__name__)
    app.register_blueprint(views_bp)
    return app
