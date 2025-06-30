from marshmallow import Schema, fields

class PlainItemSchema(Schema):
    """ item schema """
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)
      
class ItemUpdateSchema(Schema):
    """ update scehma """
    name = fields.Str(required=True)
    price = fields.Float(required=True)
    
class PlainStoreSchema(Schema):
    """ store schema """
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    
    
      
class ItemSchema(PlainItemSchema):
        store_id = fields.Int( load_only=True)
        store = fields.Nested(PlainItemSchema(), dump_only=True)

class StoreSchema(PlainStoreSchema):
    items = fields.List(fields.Nested(PlainItemSchema(), dump_only=True))

    

    