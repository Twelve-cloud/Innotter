from user.permissions import (
    IsNotAuthentificatedOrAdmin, IsUserOwnerOrAdmin, IsAdmin, IsUserOwner
)
from user.services import (
    set_blocking, block_all_users_pages, send_verification_link
)
from InnotterDjango.services import add_image_to_s3_bucket, add_url_to_request
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import AnonymousUser
from InnotterDjango.aws_s3_client import S3Client
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from user.serializers import UserSerializer
from blog.serializers import PostSerializer
from rest_framework import viewsets
from rest_framework import status
from django.urls import reverse
from user.models import User


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = []
    permission_map = {
        'create': (
            IsNotAuthentificatedOrAdmin,
        ),
        'list': (
            IsAuthenticated,
        ),
        'retrieve': (
            IsAuthenticated,
        ),
        'update': (
            IsAuthenticated,
            IsUserOwnerOrAdmin,
        ),
        'partial_update': (
            IsAuthenticated,
            IsUserOwnerOrAdmin,
        ),
        'destroy': (
            IsAuthenticated,
            IsUserOwnerOrAdmin,
        ),
        'block': (
            IsAuthenticated,
            IsAdmin,
        ),
        'liked_posts': (
            IsAuthenticated,
            IsUserOwner
        )
    }

    def get_permissions(self):
        self.permission_classes = self.permission_map.get(self.action, [])
        return super(self.__class__, self).get_permissions()

    def perform_create(self, serializer):
        user = serializer.context['request'].user
        is_verified = False if isinstance(user, AnonymousUser) else True
        serializer.save(is_verified=is_verified)

    def create(self, request, *args, **kwargs):
        if isinstance(request.user, AnonymousUser):
            link = request.build_absolute_uri(reverse('jwt-verify-email'))
            send_verification_link(link, request.data['email'])
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if 'image' in request.FILES:
            image = request.FILES.get('image')
            folder = request.user.username + '/avatar'
            add_image_to_s3_bucket(image, folder)
            url = S3Client.create_url(folder + '/' + image.name)
            add_url_to_request(url, request)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['patch'])
    def block(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        is_blocked = request.data.get('is_blocked', False)
        set_blocking(user, is_blocked)
        block_all_users_pages(user, is_blocked)
        return Response('Success', status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], serializer_class=PostSerializer)
    def liked_posts(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        self.check_object_permissions(request, user)
        liked_posts = user.liked_posts
        serializer = self.serializer_class(liked_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
