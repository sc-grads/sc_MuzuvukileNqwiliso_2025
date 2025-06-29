import uuid
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import request, jsonify
from db import stores, items

blp = Blueprint('stores', __name__, description='Operations on stores')

@blp.route('/store/<string:store_id>')
class StoreResource(MethodView):

    def get(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        store = stores.get(store_id)
        if not store:
            abort(404, message="Store not found")

        return jsonify({
            "data": store,
            "message": "Store retrieved successfully"
        })

    def put(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        data = request.get_json()
        if not data or "name" not in data:
            abort(400, message="Store name is required")

        stores[store_id]["name"] = data["name"]

        return jsonify({
            "data": stores[store_id],
            "message": "Store updated successfully"
        })

    def delete(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        deleted = stores.pop(store_id)

        # Also delete related items
        to_remove = [iid for iid, item in items.items() if item["store_id"] == store_id]
        for iid in to_remove:
            items.pop(iid)

        return jsonify({
            "data": deleted,
            "message": "Store and its items deleted successfully"
        })

@blp.route('/store')
class StoreListResource(MethodView):

    def get(self):
        return jsonify({
            "data": list(stores.values()),
            "message": "Stores retrieved successfully"
        })

    def post(self):
        data = request.get_json()
        if not data or "name" not in data:
            abort(400, message="Store name is required")

        store_id = uuid.uuid4().hex
        store = {
            "id": store_id,
            "name": data["name"],
            "items": []
        }
        stores[store_id] = store

        return jsonify({
            "data": store,
            "message": "Store created successfully"
        }), 201

@blp.route('/store/<string:store_id>/item')
class StoreItemResource(MethodView):

    def get(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        store_items = [item for item in items.values() if item['store_id'] == store_id]

        return jsonify({
            "data": store_items,
            "message": "Items retrieved successfully"
        })
