from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/")
    def home():
        return "<h1>This services has run</h1>", 200

    return app
