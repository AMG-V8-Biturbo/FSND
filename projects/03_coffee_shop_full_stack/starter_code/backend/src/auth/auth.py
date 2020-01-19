import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'hs-dev-auth.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee_shop'


# AuthError Exception
class AuthError(Exception):
    """
    AuthError Exception
    A standardized way to communicate auth failure modes
    """
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header
def get_token_auth_header():
    """
    get_token_auth_header()
        it should attempt to get the header from the request
        it should raise an AuthError if no header is present
        it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
        return the token part of the header
    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        body = {
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }
        raise AuthError(body, 401)
    auth_data = auth.split()
    if len(auth_data) != 2:
        body = {
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }
        raise AuthError(body, 401)
    elif auth_data[0].lower() != 'bearer':
        body = {
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }
        raise AuthError(body, 401)
    token = auth_data[1]
    return token


def check_permissions(permission, payload):
    """
    check_permissions(permission, payload)
        @INPUTS
            permission: string permission (i.e. 'post:drink')
            payload: decoded jwt payload

        it should raise an AuthError
        if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
        it should raise an AuthError
        if the requested permission string is not in the payload
        permissions array
        return true otherwise
    """
    if 'permissions' not in payload:
        body = {
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }
        raise AuthError(body, 400)
    elif permission not in payload['permissions']:
        body = {
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }
        raise AuthError(body, 401)
    return True


def verify_decode_jwt(token):
    """
    verify_decode_jwt(token)
        @INPUTS
            token: a json web token (string)

        it should be an Auth0 token with key id (kid)
        it should verify the token using Auth0 /.well-known/jwks.json
        it should decode the payload from the token
        it should validate the claims
        return the decoded payload
    """
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        body = {
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }
        raise AuthError(body, 401)
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if not rsa_key:
        body = {
            'code': 'invalid_header',
            'description': 'Unable to parse authentication token.'
        }
        raise AuthError(body, 400)
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer='https://' + AUTH0_DOMAIN + '/'
        )
        return payload
    except jwt.ExpiredSignatureError:
        body = {
            'code': 'token_expired',
            'description': 'Token expired.'
        }
        raise AuthError(body, 401)
    except jwt.JWTClaimsError:
        body = {
            'code': 'invalid_claims',
            'description': 'Incorrect claims. '
                           'Please, check the audience and issuer.'
        }
        raise AuthError(body, 401)
    except Exception:
        body = {
            'code': 'invalid_header',
            'description': 'Unable to parse authentication token.'
        }
        raise AuthError(body, 400)


def requires_auth(permission=''):
    """
    requires_auth(permission='')
        @INPUTS
            permission: string permission (i.e. 'post:drink')

        it should use the get_token_auth_header method to get the token
        it should use the verify_decode_jwt method to decode the jwt
        it should use the check_permissions method validate claims
        and check the requested permission
        return the decorator which passes the decoded payload to the decorated
        method
    """
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator
