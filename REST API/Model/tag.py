from db import db

class TagsModel(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    
    store_id = db.Column(
        db.Integer, 
        db.ForeignKey('store.id'), 
        nullable=False
    )

    store = db.relationship('StoreModel', back_populates='tags')
