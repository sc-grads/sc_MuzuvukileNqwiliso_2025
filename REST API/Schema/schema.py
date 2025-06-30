from marshmallow import Schema, fields


# Basic/Plain Schemas (used for nesting to avoid circular imports)
class PlainItemSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)


class PlainStoreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)


class PlainTagsSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)


# Full Schemas with relationships
class ItemSchema(PlainItemSchema):
    store_id = fields.Int(required=True, load_only=True)
    store = fields.Nested(PlainStoreSchema, dump_only=True) 


class StoreSchema(PlainStoreSchema):
    items = fields.List(fields.Nested(PlainItemSchema), dump_only=True)
    tags = fields.List(fields.Nested(PlainTagsSchema), dump_only=True)  


class TagsSchema(PlainTagsSchema):
    store_id = fields.Int(required=True, load_only=True)
    store = fields.Nested(PlainStoreSchema, dump_only=True)


class ItemUpdateSchema(Schema):
    name = fields.Str(required=True)
    price = fields.Float(required=True)
