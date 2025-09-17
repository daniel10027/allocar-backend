from marshmallow import Schema, fields

class RegisterSchema(Schema):
    email = fields.Email(required=False)
    phone = fields.String(required=False)
    password = fields.String(required=True, load_only=True)
    first_name = fields.String(required=False)
    last_name = fields.String(required=False)

class LoginSchema(Schema):
    identifier = fields.String(required=True)  # email ou phone
    password = fields.String(required=True, load_only=True)

class UserOutSchema(Schema):
    id = fields.UUID()
    email = fields.Email(allow_none=True)
    phone = fields.String(allow_none=True)
    first_name = fields.String(allow_none=True)
    last_name = fields.String(allow_none=True)
    photo_url = fields.String(allow_none=True)
    role = fields.String()
    is_active = fields.Boolean()
    is_email_verified = fields.Boolean()
    is_phone_verified = fields.Boolean()
    rating_avg = fields.Float()
    rating_count = fields.Integer()
    created_at = fields.DateTime()
