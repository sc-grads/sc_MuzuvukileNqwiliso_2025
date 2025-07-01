from flask import Flask
from flask_smorest import Api
from flask_jwt_extended import JWTManager
import os
from Resources.Store import blp as StoreBlueprint
from Resources.Item import blp as ItemsBlueprint
from Resources.Tag import blp as TagBlueprint
from Resources.User import blp as UserBlueprint

from db import db
import Model  

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
    app.config["JWT_SECRET_KEY"] = "your-secret-key"
    
    # Initialize database
    db.init_app(app)
    jwt = JWTManager(app)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            {"message": "Signature verification failed.", "error": "invalid_token"},
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            {"description": "Request does not contain an access token.", "error": "authorization_required"},
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            {"message": "The token has expired.", "error": "token_expired"},
            401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            {"message": "The token has been revoked.", "error": "token_revoked"},
            401,
        )

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_callback(jwt_header, jwt_payload):
        return (
            {"description": "The token is not fresh.", "error": "fresh_token_required"},
            401,
        )
    
    
    # Initialize API
    api = Api(app)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(ItemsBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    # Create database tables
    with app.app_context():
        import Model.store  
        import Model.item 
        import Model.tag
        import Model.user
        db.create_all()
        
    return app

# Run app directly
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
