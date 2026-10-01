from django.core.cache import cache

from users.api.utils import generate_verification_token


def test_token_is_stored_in_cache_pointing_to_user_id():
    token = generate_verification_token(user_id=42)

    # The cache key is "email_verify:<token>" and its value is the user id
    cached_user_id = cache.get(f"email_verify:{token}")
    assert cached_user_id == 42


def test_each_call_generates_a_different_token():
    token1 = generate_verification_token(user_id=1)
    token2 = generate_verification_token(user_id=1)

    # Tokens are random, even for the same user
    assert token1 != token2
