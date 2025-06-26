from flask import Flask, jsonify, request

app = Flask(__name__)

# data
stores = [
    {
        "name": "Shesha",
        "items": [
            {"name": "Relay", "price": 500},
            {"name": "Cable", "price": 200}
        ]
    },
    {
        "name": "Amazon",
        "items": [
            {"name": "Keyboard", "price": 160},
            {"name": "Mouse", "price": 80}
        ]
    },
    {
        "name": "Clicks",
        "items": [
            {"name": "Shampoo", "price": 60},
            {"name": "Toothpaste", "price": 30}
        ]
    },
    {
        "name": "Pick n Pay",
        "items": [
            {"name": "Bread", "price": 20},
            {"name": "Milk", "price": 18}
        ]
    }
]

@app.route("/stores", methods=['GET'])  # GET request
def get_stores():
    return jsonify(stores=stores)

@app.route("/stores", methods=["POST"])  # POST request
def add_store():
    request_results = request.get_json()
    new_store = {
        "name": request_results["name"],
        "items": []
    }
    stores.append(new_store)
    return jsonify(new_store), 201  # 201 Created

@app.route("/stores/<string:name>/item", methods=["POST"])
def add_items(name):
    data = request.get_json()  
    items_to_add = data.get("items", [])

    if not isinstance(items_to_add, list):
        return jsonify(message="Expected 'items' to be a list."), 400

    for store in stores:
        if store["name"].lower() == name.lower():
            for item in items_to_add:
                store["items"].append({
                    "name": item["name"],
                    "price": item["price"]
                })
            return jsonify(store), 201

    return jsonify(message="Store Not Found!"), 404

@app.get('/stores/<string:name>/item')
def get_item(name):
    for store in stores:
        if store["name"].lower() == name.lower():
            return jsonify(items=store['items'])
    return jsonify(message="Store Not Found!"), 404


if __name__ == "__main__":
    app.run(debug=True)
