from common.security import hash_password, verify_password
from .repository import get_user_by_email, get_user_by_phone, create_user
from common.errors import APIError

def register_user(email: str | None, phone: str | None, password: str, **extras):
    if not email and not phone:
        raise APIError("validation_error", "Email ou téléphone requis", 400)
    if email and get_user_by_email(email):
        raise APIError("conflict", "Email déjà utilisé", 409)
    if phone and get_user_by_phone(phone):
        raise APIError("conflict", "Téléphone déjà utilisé", 409)
    pwd = hash_password(password)
    return create_user(email=email, phone=phone, password_hash=pwd, **extras)

def authenticate(identifier: str, password: str):
    user = get_user_by_email(identifier) or get_user_by_phone(identifier)
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise APIError("invalid_credentials", "Identifiants invalides", 401)
    if not user.is_active:
        raise APIError("user_inactive", "Compte inactif", 403)
    return user
