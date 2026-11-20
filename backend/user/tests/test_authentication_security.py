"""Regression tests for JWT header handling (no live Auth0 calls)."""
from unittest.mock import Mock, patch

import pytest
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
from user.authentication import Auth0Authentication


@pytest.fixture(autouse=True)
def clear_jwks_cache():
    cache.clear()
    yield
    cache.clear()


def _jwks():
    response = Mock()
    response.json.return_value = {
        "keys": [{"kid": "expected-key", "kty": "RSA", "n": "example", "e": "AQAB"}]
    }
    return response


@pytest.mark.parametrize("algorithm", ["none", "HS256", "RS384", None])
def test_rejects_unapproved_algorithm_before_key_construction(algorithm):
    header = {"kid": "expected-key"}
    if algorithm is not None:
        header["alg"] = algorithm
    with patch("user.authentication.requests.get", return_value=_jwks()), \
         patch("user.authentication.jwt.get_unverified_header", return_value=header), \
         patch("user.authentication.jwk.construct") as construct:
        with pytest.raises(AuthenticationFailed):
            Auth0Authentication()._validate_token("untrusted")
        construct.assert_not_called()


def test_rejects_missing_kid_without_falling_back_to_first_key():
    with patch("user.authentication.requests.get", return_value=_jwks()), \
         patch("user.authentication.jwt.get_unverified_header", return_value={"alg": "RS256"}), \
         patch("user.authentication.jwk.construct") as construct:
        with pytest.raises(AuthenticationFailed):
            Auth0Authentication()._validate_token("untrusted")
        construct.assert_not_called()


def test_approved_algorithm_is_pinned_in_decode():
    with patch("user.authentication.requests.get", return_value=_jwks()), \
         patch("user.authentication.jwt.get_unverified_header",
               return_value={"alg": "RS256", "kid": "expected-key"}), \
         patch("user.authentication.jwk.construct", return_value=object()), \
         patch("user.authentication.jwt.decode", return_value={"sub": "auth0|123"}) as decode:
        assert Auth0Authentication()._validate_token("trusted") == {"sub": "auth0|123"}
        assert decode.call_args.kwargs["algorithms"] == ["RS256"]


def test_error_response_does_not_expose_validation_details():
    request = Mock()
    request.META = {"HTTP_AUTHORIZATION": "Bearer invalid"}
    with patch.object(Auth0Authentication, "_validate_token", side_effect=ValueError("secret diagnostic")):
        with pytest.raises(AuthenticationFailed) as result:
            Auth0Authentication().authenticate(request)
    assert "secret diagnostic" not in str(result.value)


@pytest.mark.parametrize("kid", ["expected-key", "rotated-key"])
def test_jwks_cache_reuses_fetch_for_repeated_validations(kid):
    keys = {"keys": [{"kid": kid, "kty": "RSA", "n": "example", "e": "AQAB"}]}
    response = Mock()
    response.json.return_value = keys
    with patch("user.authentication.requests.get", return_value=response) as get, \
         patch("user.authentication.jwt.get_unverified_header", return_value={"alg": "RS256", "kid": kid}), \
         patch("user.authentication.jwk.construct", return_value=object()), \
         patch("user.authentication.jwt.decode", return_value={"sub": "auth0|123"}):
        auth = Auth0Authentication()
        auth._validate_token("token-1")
        auth._validate_token("token-2")
        assert get.call_count == 1


def test_cache_expiration_fetches_fresh_keys():
    with patch("user.authentication.requests.get", return_value=_jwks()) as get, \
         patch("user.authentication.jwt.get_unverified_header", return_value={"alg": "RS256", "kid": "expected-key"}), \
         patch("user.authentication.jwk.construct", return_value=object()), \
         patch("user.authentication.jwt.decode", return_value={}):
        Auth0Authentication()._validate_token("first")
        cache.delete("auth0:jwks:" + __import__('user.authentication', fromlist=['AUTH0_DOMAIN']).AUTH0_DOMAIN)
        Auth0Authentication()._validate_token("after-expiration")
        assert get.call_count == 2


def test_rotated_signing_key_triggers_refresh():
    first = _jwks()
    second = Mock()
    second.json.return_value = {"keys": [{"kid": "new-key", "kty": "RSA"}]}
    with patch("user.authentication.requests.get", side_effect=[first, second]) as get, \
         patch("user.authentication.jwt.get_unverified_header", side_effect=[{"alg":"RS256","kid":"expected-key"}, {"alg":"RS256","kid":"new-key"}]), \
         patch("user.authentication.jwk.construct", return_value=object()), \
         patch("user.authentication.jwt.decode", return_value={}):
        auth = Auth0Authentication()
        auth._validate_token("old")
        auth._validate_token("new")
        assert get.call_count == 2


def test_unknown_kid_cannot_force_unlimited_jwks_refreshes():
    with patch("user.authentication.requests.get", return_value=_jwks()) as get, \
         patch("user.authentication.jwt.get_unverified_header", return_value={"alg":"RS256","kid":"attacker-key"}):
        for _ in range(3):
            with pytest.raises(AuthenticationFailed):
                Auth0Authentication()._validate_token("bad")
        assert get.call_count == 2  # initial request + one cooldown-limited refresh


def test_bad_jwks_response_is_not_cached():
    response = Mock()
    response.json.return_value = {"malformed": "response"}
    with patch("user.authentication.requests.get", return_value=response) as get, \
         patch("user.authentication.jwt.get_unverified_header", return_value={"alg":"RS256","kid":"expected-key"}):
        for _ in range(2):
            with pytest.raises(AuthenticationFailed):
                Auth0Authentication()._validate_token("token")
        assert get.call_count == 2
