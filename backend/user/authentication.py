import os
import logging
import requests
from django.core.cache import cache
from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

# Auth0 configuration - must be set via environment variables
AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID')
AUTH0_AUDIENCE = os.environ.get('AUTH0_AUDIENCE')

# Validate required environment variables
if not AUTH0_DOMAIN:
    raise ValueError('AUTH0_DOMAIN environment variable is required')
if not AUTH0_AUDIENCE:
    raise ValueError('AUTH0_AUDIENCE environment variable is required')


# Public Auth0 signing keys are cached briefly; the JWT itself is never cached.
JWKS_CACHE_SECONDS = 300
JWKS_REFRESH_COOLDOWN_SECONDS = 30
JWKS_CACHE_KEY = f'auth0:jwks:{AUTH0_DOMAIN}'
JWKS_REFRESH_KEY = f'{JWKS_CACHE_KEY}:refresh'


def _get_jwks(force_refresh=False):
    """Fetch/validate JWKS and cache it. Force-refresh is rate-limited for unknown kids."""
    if not force_refresh:
        cached = cache.get(JWKS_CACHE_KEY)
        if cached is not None:
            return cached
    else:
        # An attacker can choose arbitrary JWT key IDs. Limit their network impact.
        if not cache.add(JWKS_REFRESH_KEY, True, timeout=JWKS_REFRESH_COOLDOWN_SECONDS):
            return cache.get(JWKS_CACHE_KEY)

    try:
        response = requests.get(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json', timeout=10)
        response.raise_for_status()
        jwks = response.json()
        if not isinstance(jwks, dict) or not isinstance(jwks.get('keys'), list):
            raise ValueError('Unexpected JWKS response')
        cache.set(JWKS_CACHE_KEY, jwks, timeout=JWKS_CACHE_SECONDS)
        return jwks
    except (requests.RequestException, ValueError) as exc:
        logger.warning('Unable to refresh Auth0 JWKS', exc_info=True)
        raise exceptions.AuthenticationFailed('Invalid authentication token') from exc


class Auth0Authentication(authentication.BaseAuthentication):
    """
    Auth0 JWT authentication class for Django REST Framework.
    Validates the JWT from Auth0 and extracts the user email and roles.
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None
        
        try:
            payload = self._validate_token(token)
        except Exception:
            logger.warning('Auth0 authentication failed', exc_info=True)
            raise exceptions.AuthenticationFailed('Invalid authentication token')
        
        # Try to get email from custom claim first (access token)
        email = payload.get('https://backend-api-capstone/email')
        # Fallback to standard email claim (ID token)
        if not email:
            email = payload.get('email')
        # Last resort - use sub (user ID)
        if not email:
            email = payload.get('sub', '')
        
        user_info = {
            'email': email,
            'sub': payload.get('sub', ''),
            'roles': payload.get('https://backend-api-capstone/roles', []),
        }
        
        return (UserWrapper(user_info), token)

    def _validate_token(self, token):
        """Validate the JWT token against Auth0's public key."""
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception as e:
            logger.error(f'Failed to get token header: {e}')
            raise Exception('Invalid token header')
        
        # Never trust the algorithm supplied by an untrusted JWT header.
        if unverified_header.get('alg') != 'RS256':
            raise exceptions.AuthenticationFailed('Invalid authentication token')
        
        token_kid = unverified_header.get('kid')
        if not token_kid:
            raise exceptions.AuthenticationFailed('Invalid authentication token')

        jwks = _get_jwks()
        if not any(k.get('kid') == token_kid and k.get('kty') == 'RSA'
                   for k in jwks.get('keys', [])):
            # Auth0 rotates keys. Refresh once when the known key set is stale.
            jwks = _get_jwks(force_refresh=True) or jwks

        rsa_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == token_kid and key.get('kty') == 'RSA':
                rsa_key = jwk.construct(key)
                break
        if not rsa_key:
            raise exceptions.AuthenticationFailed('Invalid authentication token')
        
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=['RS256'],
                audience=AUTH0_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/',
            )
        except ExpiredSignatureError:
            raise Exception('Token has expired')
        except JWTClaimsError as e:
            raise Exception(f'Invalid token claims: {str(e)}')
        except Exception as e:
            logger.error(f'Token validation failed: {str(e)}')
            raise Exception(f'Token validation failed: {str(e)}')
        
        return payload


class UserWrapper:
    """
    A simple wrapper class to represent an authenticated user.
    """
    def __init__(self, user_info):
        self.user_info = user_info
        self.email = user_info.get('email', '')
        self.sub = user_info.get('sub', '')
        self.roles = user_info.get('roles', [])
        self.is_authenticated = True
    
    def __str__(self):
        return self.email
    
    def has_role(self, role):
        """Check if user has a specific role."""
        role_lower = role.lower()
        return any(r.lower() == role_lower for r in self.roles)
    
    def get_role(self):
        """Get the user's first role."""
        if self.roles:
            return self.roles[0].lower()
        return None

