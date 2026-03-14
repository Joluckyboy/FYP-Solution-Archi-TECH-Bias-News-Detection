from flask import Flask
from fastapi import FastAPI, HTTPException
from flask_cors import CORS
import os
from dotenv import load_dotenv
from .functions.get_model import get_model

# Other extensions (e.g., login_manager, migrate) are initialized here but not yet bound to an app instance

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_mapping(
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # import blueprints
    from .blueprints.biasengine import biasengine

    app.register_blueprint(biasengine)

    # get model
    model_components = get_model()
    app.device = model_components["device"]
    app.tokenizer = model_components["tokenizer"]
    app.model = model_components['model']

    # set perplexity api key
    load_dotenv()
    app.pkey = os.environ.get('API_KEY') or os.environ.get('KEY')

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    return app