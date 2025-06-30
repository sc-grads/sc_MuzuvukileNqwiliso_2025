from db import db

class ItemModel(db.Model):
    __tablename__ = 'item'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    store = db.relationship('StoreModel', back_populates='items')
    """ back_populates='items' => this means that this column 'items' correspond with the items column
     in StoreModel class """
