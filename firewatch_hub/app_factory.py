import flask
import logging
from pathlib import Path

from .configuration import Configuration
from .model import get_model_from_conf
from .views import bp as views_bp


logger = logging.getLogger(__name__)


def get_app(conf_file_path):
    logger.info('Initializing app with config %s', conf_file_path)

    conf = Configuration(Path(conf_file_path))
    model = get_model_from_conf(conf)

    app = flask.Flask(__name__)
    app.secret_key = conf.secret_file.get_value()

    app.register_blueprint(views_bp)

    @app.before_request
    def before():
        flask.g.conf = conf
        flask.g.model = model

    return app
