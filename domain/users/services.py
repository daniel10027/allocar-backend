from common.security import hash_password, verify_password
from .repository import get_user_by_email, get_user_by_phone, create_user
from common.errors import APIError
from extensions.db import db
from .models import User
from common.otp import set_otp_for_email, set_otp_for_phone, verify_email_otp, verify_phone_otp
from common.otp import (
    set_reset_otp, verify_reset_otp,
    issue_reset_token, consume_reset_token
)
from .tasks import send_email_reset_otp_task, send_sms_otp_task, send_email_otp_task

def _send_otp_for_user(user: User):
    # génère et envoie les OTP selon les canaux renseignés
    if user.email:
        try:
            code = set_otp_for_email(user.email)
            send_email_otp_task.delay(user.email, code)
        except RuntimeError as e:
            if str(e) != "otp_resend_too_soon":
                raise
    if user.phone:
        try:
            code = set_otp_for_phone(user.phone)
            send_sms_otp_task.delay(user.phone, code)
        except RuntimeError as e:
            if str(e) != "otp_resend_too_soon":
                raise

def register_user(email: str | None, phone: str | None, password: str, **extras):
    if not email and not phone:
        raise APIError("validation_error", "Email ou téléphone requis", 400)
    if email and get_user_by_email(email):
        raise APIError("conflict", "Email déjà utilisé", 409)
    if phone and get_user_by_phone(phone):
        raise APIError("conflict", "Téléphone déjà utilisé", 409)
    pwd = hash_password(password)
    user = create_user(email=email, phone=phone, password_hash=pwd, **extras)
    # au départ, flags vérif restent False => envoi OTP
    _send_otp_for_user(user)
    return user

def authenticate(identifier: str, password: str):
    user = get_user_by_email(identifier) or get_user_by_phone(identifier)
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise APIError("invalid_credentials", "Identifiants invalides", 401)
    # Bloquer la connexion si un canal renseigné n'est pas vérifié
    if user.email and not user.is_email_verified:
        raise APIError("email_not_verified", "Veuillez vérifier votre e-mail", 403)
    if user.phone and not user.is_phone_verified:
        raise APIError("phone_not_verified", "Veuillez vérifier votre numéro de téléphone", 403)
    if not user.is_active:
        raise APIError("user_inactive", "Compte inactif", 403)
    return user

def request_otp_for_user(user: User, email: str | None, phone: str | None):
    # permet de redemander les OTP (avec cooldown)
    if email:
        code = set_otp_for_email(email)
        send_email_otp_task.delay(email, code)
    if phone:
        code = set_otp_for_phone(phone)
        send_sms_otp_task.delay(phone, code)
    return True

def verify_otp_and_mark(user: User, channel: str, identifier: str, code: str) -> bool:
    ok = False
    if channel == "email":
        if not user.email or user.email.lower() != identifier.lower():
            raise APIError("validation_error", "Email ne correspond pas au compte", 400)
        ok = verify_email_otp(identifier, code)
        if ok:
            user.is_email_verified = True
    elif channel == "phone":
        if not user.phone or user.phone != identifier:
            raise APIError("validation_error", "Téléphone ne correspond pas au compte", 400)
        ok = verify_phone_otp(identifier, code)
        if ok:
            user.is_phone_verified = True
    else:
        raise APIError("validation_error", "Canal invalide", 400)

    if not ok:
        raise APIError("otp_invalid", "Code OTP invalide ou expiré", 400)

    db.session.commit()
    return True

def request_password_reset(identifier: str, channels: list[str]):
    """
    Envoie des OTP de reset sur les canaux demandés (si l'utilisateur existe).
    Retourne toujours success pour éviter l'enumération.
    """
    user = get_user_by_email(identifier) or get_user_by_phone(identifier)
    if not user:
        # réponse générique
        return True

    # On ne force pas la correspondance stricte canal/identifiant ; on envoie si possible.
    if "email" in channels and user.email:
        try:
            code = set_reset_otp(user.email, "email")
            send_email_reset_otp_task.delay(user.email, code)
        except RuntimeError as e:
            if str(e) != "otp_resend_too_soon":
                raise
    if "sms" in channels and user.phone:
        try:
            code = set_reset_otp(user.phone, "sms")
            send_sms_otp_task.delay(user.phone, code)
        except RuntimeError as e:
            if str(e) != "otp_resend_too_soon":
                raise
    return True

def verify_reset_otp_and_issue_token(identifier: str, channel: str, code: str) -> str:
    """
    Vérifie le code OTP de reset, puis émet un reset_token opaque (stocké Redis).
    """
    # vérifie que l'utilisateur existe et que l'identifier correspond bien au canal
    user = get_user_by_email(identifier) if channel == "email" else get_user_by_phone(identifier)
    if not user:
        raise APIError("not_found", "Utilisateur introuvable", 404)
    ok = verify_reset_otp(identifier, channel, code)
    if not ok:
        raise APIError("otp_invalid", "Code OTP invalide ou expiré", 400)
    return issue_reset_token(identifier)

def reset_password_with_token(identifier: str, reset_token: str, new_password: str):
    user = get_user_by_email(identifier) or get_user_by_phone(identifier)
    if not user:
        raise APIError("not_found", "Utilisateur introuvable", 404)
    if not consume_reset_token(identifier, reset_token):
        raise APIError("invalid_token", "Jeton de réinitialisation invalide ou expiré", 400)
    user.password_hash = hash_password(new_password)
    db.session.commit()
    return True

def change_password(user_id, old_password: str, new_password: str):
    u = db.session.get(User, user_id)
    if not u:
        raise APIError("not_found", "Utilisateur introuvable", 404)
    if not verify_password(old_password, u.password_hash):
        raise APIError("invalid_credentials", "Ancien mot de passe incorrect", 401)
    u.password_hash = hash_password(new_password)
    db.session.commit()
    return True
