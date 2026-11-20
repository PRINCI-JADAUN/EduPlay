import uuid

import jwt
from django.conf import settings
from jwt.exceptions import InvalidTokenError


class IdentityError(Exception):
    def __init__(self, message, status=401):
        self.message = message
        self.status = status
        super().__init__(message)


def player_id_for(request, data=None):
    authorization = request.headers.get("Authorization", "")
    token = authorization.removeprefix("Bearer ").strip() if authorization.startswith("Bearer ") else ""

    if settings.SUPABASE_URL or settings.SUPABASE_JWT_SECRET:
        if not token or not settings.SUPABASE_JWT_SECRET:
            raise IdentityError("A valid Supabase access token is required.")
        try:
            claims = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"require": ["sub"]},
            )
            return uuid.UUID(claims["sub"])
        except (InvalidTokenError, ValueError, TypeError):
            raise IdentityError("The Supabase access token is invalid.") from None

    if not settings.LOCAL_DEMO_MODE:
        raise IdentityError("Authentication is not configured.")

    raw_id = (data or {}).get("player_id") or request.GET.get("player_id")
    try:
        return uuid.UUID(str(raw_id))
    except (ValueError, TypeError, AttributeError):
        raise IdentityError("A valid player_id is required in local demo mode.", status=400) from None

