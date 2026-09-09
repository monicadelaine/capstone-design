import os
import logging
import requests
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
        except Exception as e:
            raise exceptions.AuthenticationFailed(str(e))
        
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
        jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
        
        try:
            jwks_response = requests.get(jwks_url, timeout=10)
            jwks = jwks_response.json()
        except Exception as e:
            logger.error(f'Unable to fetch JWKS: {e}')
            raise Exception('Unable to fetch JWKS')
        
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception as e:
            logger.error(f'Failed to get token header: {e}')
            raise Exception('Invalid token header')
        
        # Get algorithm from token header, default to RS256
        token_alg = unverified_header.get('alg', 'RS256')
        
        rsa_key = {}
        token_kid = unverified_header.get('kid')
        
        # If token has no kid, try to use the first key from JWKS
        if not token_kid and jwks.get('keys'):
            key = jwks['keys'][0]
            rsa_key = jwk.construct(key)
        else:
            for key in jwks.get('keys', []):
                if key.get('kid') == token_kid:
                    rsa_key = jwk.construct(key)
                    break
        
        if not rsa_key:
            jwks_kids = [key.get('kid') for key in jwks.get('keys', [])]
            raise Exception(f'Unable to find appropriate key. Token kid: {token_kid}, Available kids: {jwks_kids}')
        
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=[token_alg],
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

