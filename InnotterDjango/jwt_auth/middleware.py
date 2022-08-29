from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from jwt_auth.services import create_response, get_payload_by_token
from rest_framework import status
from user.models import User
import jwt


class JWTMiddleware:
    def __init__(self, next):
        self.next = next

    def __call__(self, request):
        access_token = request.COOKIES.get('access_token', None)

        if access_token:
            try:
                payload = get_payload_by_token(access_token)

                if payload is None:
                    raise AuthenticationFailed(data={'Error': 'Unauthorized'})

                request.user = User.objects.get(pk=payload.get('sub'))

                if request.user.is_blocked:
                    raise PermissionDenied(detail={'Error': 'User is blocked'})

                # If front-end will get HTTP_401_UNAUTHORIZED
                # It'll delete access token from cookie and
                # set refresh token to a cookie and request to
                # /auth/jwt/refresh to get new tokens

        response = self.next(request)
        return response
