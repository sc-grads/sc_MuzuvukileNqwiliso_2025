from marshmallow import Schema, fields

class ItemSchema(Schema):
    """ item schema """
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)
    store_id = fields.Str(required=True)
      
class ItemUpdateSchema(Schema):
    """ update scehma """
    name = fields.Str(required=True)
    price = fields.Float(required=True)
    
class StoreSchema(Schema):
    """ store schema """
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)