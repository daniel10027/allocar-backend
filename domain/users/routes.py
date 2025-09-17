from flask_smorest import Blueprint
from common.responses import ok
from common.errors import APIError
from .schemas import RegisterSchema, LoginSchema, UserOutSchema
from .services import register_user, authenticate
from extensions.db import db
from flask_jwt_extended import jwt_required, get_jwt_identity, create_refresh_token, create_access_token, get_jwt
from datetime import datetime, timezone
from common.jwt_blocklist import revoke
from extensions.s3 import get_s3_client
from flask import current_app

blp = Blueprint("users", __name__, description="Users & Auth")

@blp.route("/auth/register", methods=["POST"])
@blp.arguments(RegisterSchema)
@blp.response(201, UserOutSchema)
def register(payload):
    user = register_user(
        email=payload.get("email"),
        phone=payload.get("phone"),
        password=payload["password"],
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
    )
    return user.to_dict()

@blp.route("/auth/login", methods=["POST"])
@blp.arguments(LoginSchema)
def login(payload):
    user = authenticate(payload["identifier"], payload["password"])
    access = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh = create_refresh_token(identity=str(user.id))
    return ok({"access_token": access, "refresh_token": refresh, "user": user.to_dict()})

@blp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_jwt_identity()
    # recherche par email/phone non nécessaire, on fait une query simple par id
    from .models import User
    user = db.session.get(User, uid)
    if not user:
        raise APIError("not_found", "User not found", 404)
    return ok(user.to_dict())


@blp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def token_refresh():
    uid = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role") or "user"
    access = create_access_token(identity=str(uid), additional_claims={"role": role})
    return ok({"access_token": access})

@blp.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    j = get_jwt()
    exp = int(j.get("exp", 0)) - int(datetime.now(timezone.utc).timestamp())
    revoke(j.get("jti"), max(exp, 0))
    return ok({"logout": True})


@blp.route("/me/photo", methods=["POST"])
@jwt_required()
def me_photo_presign():
    uid = get_jwt_identity()
    s3 = get_s3_client(current_app)
    bucket = current_app.config.get("S3_BUCKET")
    key = f"users/{uid}/photo.jpg"
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": "image/jpeg"},
        ExpiresIn=3600,
    )
    return ok({"upload_url": url, "key": key})
