from flask import Flask, jsonify, request
from flask_smorest import abort
from db import stores, items
import uuid

app = Flask(__name__)

# GET all stores
@app.route("/stores", methods=['GET'])
def get_stores():
    return jsonify(stores=list(stores.values()))


@app.get("/stores/<string:store_id>")
def get_store(store_id):
    store = stores.get(store_id)
    if store:
        return jsonify(store)
    abort(404,message="Store Not Found!")


# POST: Add a store
@app.route("/stores", methods=["POST"])
def add_store():
    request_data = request.get_json()
    store_id = uuid.uuid4().hex
    store = {
        **request_data,
        "id": store_id,
        "items": []
    }
    stores[store_id] = store
    return jsonify(store), 201


# POST: Add an item to a store
@app.post('/item')
def add_items():
    item_data = request.get_json()
    print(item_data)
    store_id = item_data.get("store_id")

    if store_id not in stores:
        abort(404, message="Store Not Found!")

    item_id = uuid.uuid4().hex
    item = {
        **item_data,
        "id": item_id
    }

    items[item_id] = item
    stores[store_id]["items"].append(item)  # Add to store's item list

    return jsonify(item), 201



# GET: Items for a specific store
@app.get('/stores/<string:store_id>/item')
def get_item(store_id):
    if store_id in stores:
        return jsonify(items=stores[store_id]["items"])
    return jsonify(message="Store Not Found!"), 404


if __name__ == "__main__":
    app.run(debug=True)
