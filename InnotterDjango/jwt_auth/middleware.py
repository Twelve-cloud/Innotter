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
                request.user = User.objects.get(pk=payload.get('id'))

                if request.user.is_blocked:
                    return create_response(
                        data={'Error': 'User is blocked'},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            except jwt.ExpiredSignatureError:
                return create_response(
                    data={'Error': 'Unauthorized'},
                    status=status.HTTP_401_UNAUTHORIZED,
                    hdrs={'WWW-Authenticate': 'Refresh token'}
                )
                # If front-end will get HTTP_401_UNAUTHORIZED
                # It'll delete access token from cookie and
                # set refresh token to a cookie and request to
                # /auth/jwt/refresh to get new tokens

        response = self.next(request)
        return response
