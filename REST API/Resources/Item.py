import uuid
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import request, jsonify
from db import items, stores
from Schema.schema import ItemSchema, ItemUpdateSchema

blp = Blueprint('items', __name__, description='Operations on items')


@blp.route('/items/<string:store_id>')
class ItemsListResource(MethodView):
    # POST: Add items to a specific store
    @blp.arguments(ItemSchema)
    def post(self, store_id):
        data = request.get_json()

        if not data or "items" not in data:
            abort(400, message="Request must include an 'items' list")

        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        if not isinstance(data["items"], list) or not data["items"]:
            abort(400, message="Items must be a non-empty list")

        created_items = []

        for item in data["items"]:
            if "name" not in item or "price" not in item:
                abort(400, message="Each item must include name and price")
            if not isinstance(item["price"], (int, float)) or item["price"] < 0:
                abort(400, message="Item price must be a non-negative number")

            item_id = uuid.uuid4().hex
            new_item = {
                "id": item_id,
                "name": item["name"],
                "price": item["price"],
                "store_id": store_id
            }

            items[item_id] = new_item
            stores[store_id]["items"].append(new_item)
            created_items.append(new_item)

        return jsonify({
            "data": created_items,
            "message": "Items added successfully"
        }), 201


@blp.route('/store/<string:store_id>/items')
class StoreItemsResource(MethodView):
    # GET: Retrieve items for a specific store
    def get(self, store_id):
        try:
            uuid.UUID(store_id)
        except ValueError:
            abort(400, message="Invalid store ID format")

        if store_id not in stores:
            abort(404, message="Store not found")

        return jsonify({
            "data": stores[store_id]["items"],
            "message": "Items retrieved successfully"
        })


@blp.route('/item/<string:item_id>')
class ItemUpdateResource(MethodView):
    # PUT: Update a single item
    @blp.arguments(ItemUpdateSchema)
    def put(self, item_id):
        try:
            uuid.UUID(item_id)
        except ValueError:
            abort(400, message="Invalid item ID format")

        if item_id not in items:
            abort(404, message="Item not found")

        data = request.get_json()
        if "name" not in data or "price" not in data:
            abort(400, message="Request must include name and price")
        if not isinstance(data["price"], (int, float)) or data["price"] < 0:
            abort(400, message="Item price must be a non-negative number")

        item = items[item_id]
        item["name"] = data["name"]
        item["price"] = data["price"]

        for i in stores[item["store_id"]]["items"]:
            if i["id"] == item_id:
                i["name"] = data["name"]
                i["price"] = data["price"]
                break

        return jsonify({
            "data": item,
            "message": "Item updated successfully"
        })

    # DELETE: Remove a single item
    def delete(self, item_id):
        try:
            uuid.UUID(item_id)
        except ValueError:
            abort(400, message="Invalid item ID format")

        if item_id not in items:
            abort(404, message="Item not found")

        item = items.pop(item_id)
        store_id = item["store_id"]
        stores[store_id]["items"] = [i for i in stores[store_id]["items"] if i["id"] != item_id]

        return jsonify({
            "data": item,
            "message": "Item deleted successfully"
        })
