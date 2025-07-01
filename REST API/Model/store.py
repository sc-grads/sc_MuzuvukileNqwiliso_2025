from db import db

class StoreModel(db.Model):
    __tablename__ = 'store'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    items = db.relationship(
        'ItemModel', 
        back_populates='store', 
        lazy='dynamic', 
        cascade='all, delete'
    )

    tags = db.relationship(
        'TagsModel', 
        back_populates='store', 
        lazy='dynamic', 
        cascade='all, delete'
    )

    """ back_populates='store' => this means that this 'store' is the column in the ItemModel """
    """ what does the lazy= 'dynamic' mean?
     
    Don’t automatically fetch the items when I load a store. Instead, give me a 
    query object that I can further filter or control before fetching
    
    """