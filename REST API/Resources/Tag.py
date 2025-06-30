from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from db import db
from Model import StoreModel, TagsModel
from Schema.schema import TagsSchema

blp = Blueprint("tags", __name__, description="Operations on tags")

@blp.route("/store/<int:store_id>/tag")
class TagResources(MethodView):

    @blp.response(200, TagsSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id, description="Store not found")
        return store.tags.all()  

    @blp.arguments(TagsSchema)
    @blp.response(201, TagsSchema)
    def post(self, tag_data, store_id):
        tag = TagsModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
        except IntegrityError:
            abort(400, message="Tag with that name already exists in this store.")
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        return tag

@blp.route("/tag/<int:tag_id>")
class TagResource(MethodView):

    @blp.response(200, TagsSchema)
    def get(self, tag_id):
        tag = TagsModel.query.get_or_404(tag_id, description="Tag not found")
        return tag
