import uuid
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy.exc import SQLAlchemyError
from Schema.schema import StoreSchema, PlainItemSchema
from Model.store import StoreModel
from db import db

blp = Blueprint('stores', __name__, description='Operations on stores')


@blp.route('/store/<int:store_id>')
class StoreResource(MethodView):

    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id, description="Store not found")
        return store

    @blp.arguments(StoreSchema)
    @blp.response(200, StoreSchema)
    def put(self, store_data, store_id):
        store = StoreModel.query.get(store_id)
        if not store:
            abort(404, message="Store not found")

        store.name = store_data["name"]

        try:
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Failed to update store")

        return store

    @blp.response(200)
    def delete(self, store_id):
        store = StoreModel.query.get(store_id)
        if not store:
            abort(404, message="Store not found")

        try:
            db.session.delete(store)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Failed to delete store")

        return {
            "message": "Store and its items deleted successfully"
        }


@blp.route('/store')
class StoreListResource(MethodView):

    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        new_store = StoreModel(name=store_data["name"])

        try:
            db.session.add(new_store)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Failed to create store")

        return new_store


@blp.route('/store/<int:store_id>/item')
class StoreItemResource(MethodView):

    @blp.response(200, PlainItemSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get(store_id)
        if not store:
            abort(404, message="Store not found")

        return store.items
