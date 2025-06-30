import uuid
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy.exc import SQLAlchemyError
from db import db
from Model import ItemModel, StoreModel
from Schema.schema import ItemSchema, ItemUpdateSchema

blp = Blueprint('items', __name__, description='Operations on items')


@blp.route('/items/<int:store_id>')
class ItemsListResource(MethodView):
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data, store_id):
        store = StoreModel.query.get(store_id)
        if not store:
            abort(404, message="Store not found")

        item = ItemModel(**item_data, store_id=store_id)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=f"Error saving item: {str(e)}")

        return item


@blp.route('/store/<int:store_id>/items')
class StoreItemsResource(MethodView):
    @blp.response(200, ItemSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get(store_id)
        if not store:
            abort(404, message="Store not found")

        return store.items


@blp.route('/item/<int:item_id>')
class ItemUpdateResource(MethodView):
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemModel.query.get(item_id)
        if not item:
            abort(404, message="Item not found")

        item.name = item_data["name"]
        item.price = item_data["price"]

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=f"Failed to update item: {str(e)}")

        return item

    @blp.response(200, ItemSchema)
    def delete(self, item_id):
        item = ItemModel.query.get(item_id)
        if not item:
            abort(404, message="Item not found")

        try:
            db.session.delete(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=f"Failed to delete item: {str(e)}")

        return item
