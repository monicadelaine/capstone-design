"""Regression tests for JWT header handling (no live Auth0 calls)."""
from unittest.mock import Mock, patch

import pytest
from rest_framework.exceptions import AuthenticationFailed
from user.authentication import Auth0Authentication


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
