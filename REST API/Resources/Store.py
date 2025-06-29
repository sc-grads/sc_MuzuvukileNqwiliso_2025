import uuid
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import jsonify
from db import stores, items
from Schema.schema import StoreSchema

blp = Blueprint('stores', __name__, description='Operations on stores')

@blp.route('/store/<string:store_id>')
class StoreResource(MethodView):

    @blp.response(200, StoreSchema)
    def get(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        store = stores.get(store_id)
        if not store:
            abort(404, message="Store not found")

        return store

    @blp.arguments(StoreSchema)
    @blp.response(200, StoreSchema)
    def put(self, store_data, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        stores[store_id]["name"] = store_data["name"]

        return stores[store_id]

    @blp.response(200)
    def delete(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        deleted = stores.pop(store_id)

        # Remove associated items
        to_remove = [iid for iid, item in items.items() if item["store_id"] == store_id]
        for iid in to_remove:
            items.pop(iid)

        return {
            "data": deleted,
            "message": "Store and its items deleted successfully"
        }

@blp.route('/store')
class StoreListResource(MethodView):

    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return list(stores.values())

    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store_id = uuid.uuid4().hex
        store = {
            "id": store_id,
            "name": store_data["name"],
            "items": []
        }
        stores[store_id] = store
        return store

@blp.route('/store/<string:store_id>/item')
class StoreItemResource(MethodView):

    @blp.response(200)
    def get(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        store_items = [item for item in items.values() if item['store_id'] == store_id]

        return {
            "data": store_items,
            "message": "Items retrieved successfully"
        }
