from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy.exc import SQLAlchemyError
from db import db
from Model.user import UserModel
from Schema.schema import UserRegisterSchema, UserSchema, UserLoginSchema
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, jwt_required

blp = Blueprint("users",__name__, description="Operations on users")

@blp.route("/userRegister")
class UserResource(MethodView):
    @blp.arguments(UserRegisterSchema) 
    @blp.response(201,UserSchema) 
    def post(self,user_data):
    
        if UserModel.query.filter_by(username=user_data['username']).first():
            abort(409, message="A user with that username already exists.")

        hashed_password = pbkdf2_sha256.hash(user_data['password'])

        user = UserModel(
            username = user_data['username'],
            password = hashed_password 
        )
        
        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as e:
             abort(500, message=str(e))
        
        return user
    
    @blp.route("/user/<int:user_id>")
    @jwt_required()
    @blp.response(200,UserSchema)
    def get(self,user_id):
        user = UserModel.query.get_or_404(user_id)
        
        return user
    
    @blp.route("/user/<int:user_id>")
    @jwt_required()
    @blp.response(200)
    def delete(self,user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        
        return {"message": "User deleted."}

@blp.route("/user/login")
class UserLogin(MethodView):
    @blp.arguments(UserLoginSchema)
    def post(self, user_data):
        user = UserModel.query.filter_by(username=user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id)
            return {"access_token": access_token}
        else:
            abort(401, message="Invalid credentials.")
