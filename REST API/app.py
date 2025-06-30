from flask import Flask
from flask_smorest import Api
import os
from Resources.Store import blp as StoreBlueprint
from Resources.Item import blp as ItemsBlueprint

from db import db
import Model  # This ensures your models are registered with SQLAlchemy

def create_app(db_url=None):
    app = Flask(__name__)

    # Configuration
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Store API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URI", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database
    db.init_app(app)

    # Initialize API
    api = Api(app)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(ItemsBlueprint)

    # Create database tables
    with app.app_context():
        import Model.store  # or from Model import StoreModel
        import Model.item   # make sure models are imported
        db.create_all()
        
    return app

# Run app directly
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
