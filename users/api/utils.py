import secrets

from django.core.cache import cache


def generate_verification_token(user_id: int) -> str:
    """Create a one-time email verification token for the given user."""
    # URL-safe random string, hard to guess
    token = secrets.token_urlsafe(32)
    cache_key = f"email_verify:{token}"
    # Map token -> user id in Redis; it expires on its own after 900s (15 min)
    cache.set(cache_key, user_id, timeout=900)
    return token
