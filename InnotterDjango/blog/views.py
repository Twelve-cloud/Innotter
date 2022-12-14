from blog.permissions import (
    IsPageNotPrivate, IsPageNotBlocked, IsPageOwner,
    IsPageOwnerOrAdmin, IsPageOwnerOrAdminOrModerator,
    IsNotPageOwner, IsPagePrivate
)
from blog.services import (
    set_blocking, follow_page, like_or_unlike_post,
    add_user_to_followers, add_all_users_to_followers,
    remove_user_from_requests, remove_all_users_from_requests,
    send_notification_to_followers
)
from InnotterDjango.services import add_image_to_s3_bucket, add_url_to_request
from blog.serializers import TagSerializer, PageSerializer, PostSerializer
from rest_framework.permissions import IsAuthenticated
from InnotterDjango.aws_s3_client import S3Client
from user.permissions import IsAdminOrModerator
from django.shortcuts import get_object_or_404
from blog.exceptions import InvalidFilterType
from rest_framework.decorators import action
from rest_framework.response import Response
from user.serializers import UserSerializer
from rest_framework import viewsets, mixins
from blog.models import Tag, Page, Post
from rest_framework import generics
from rest_framework import status
from user.models import User
from itertools import chain


class TagViewSet(mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = []
    permission_map = {
        'create': (
            IsAuthenticated,
            IsAdminOrModerator,
        ),
        'list': (
            IsAuthenticated,
        ),
        'retrieve': (
            IsAuthenticated,
        ),
        'destroy': (
            IsAuthenticated,
            IsAdminOrModerator,
        ),
    }

    def get_permissions(self):
        self.permission_classes = self.permission_map.get(self.action, [])
        return super(self.__class__, self).get_permissions()


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = []
    permission_map = {
        'create': (
            IsAuthenticated,
        ),
        'list': (
            IsAuthenticated,
        ),
        'retrieve': (
            IsAuthenticated,
            IsPageNotPrivate,
            IsPageNotBlocked,
        ),
        'update': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
        ),
        'partial_update': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
        ),
        'destroy': (
            IsAuthenticated,
            IsPageOwnerOrAdmin,
        ),
        'block': (
            IsAuthenticated,
            IsAdminOrModerator,
        ),
        'follow': (
            IsAuthenticated,
            IsPageNotBlocked,
            IsNotPageOwner
        ),
        'requests': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
            IsPagePrivate
        ),
        'accept': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
            IsPagePrivate
        ),
        'accept_all': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
            IsPagePrivate
        ),
        'decline': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
            IsPagePrivate
        ),
        'decline_all': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
            IsPagePrivate
        ),
        'search': (
            IsAuthenticated,
        )
    }

    def get_permissions(self):
        self.permission_classes = self.permission_map.get(self.action, [])
        return super(self.__class__, self).get_permissions()

    def create(self, request, *args, **kwargs):
        if 'image' in request.FILES:
            image = request.FILES.get('image')
            folder = request.user.username + '/pages/' + request.data.get('uuid')
            add_image_to_s3_bucket(image, folder)
            url = S3Client.create_url(folder + '/' + image.name)
            add_url_to_request(url, request)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if 'image' in request.FILES:
            image = request.FILES.get('image')
            page = Page.objects.get(pk=kwargs.get('pk'))
            folder = request.user.username + '/pages/' + page.uuid
            add_image_to_s3_bucket(image, folder)
            url = S3Client.create_url(folder + '/' + image.name)
            add_url_to_request(url, request)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['patch'])
    def block(self, request, pk=None):
        page = get_object_or_404(Page, pk=pk)
        set_blocking(page, request.data.get('unblock_date', None))
        return Response('Success', status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def follow(self, request, pk=None):
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        follow_page(page, request.user)
        return Response('Success', status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def requests(self, request, pk=None):
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        serializer = self.serializer_class(page)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def accept(self, request, pk=None):
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        add_user_to_followers(page, request.data.get('user_id', None))
        return Response('Success', status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def accept_all(self, request, pk=None):
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        add_all_users_to_followers(page)
        return Response('Success', status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def decline(self, request, pk=None):
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        remove_user_from_requests(page, request.data.get('user_id', None))
        return Response('Success', status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def decline_all(self, request, pk=None):
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        remove_all_users_from_requests(page)
        return Response('Success', status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def news(self, request):
        pages = request.user.pages.all() | request.user.follows.all()
        posts = list(chain(*[page.posts.all() for page in pages]))
        posts.sort(key=lambda post: post.created_at, reverse=True)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = []
    permission_map = {
        'create': (
            IsAuthenticated,
            IsPageOwner,
        ),
        'list': (
            IsAuthenticated,
            IsPageNotPrivate,
            IsPageNotBlocked,
        ),
        'retrieve': (
            IsAuthenticated,
            IsPageNotPrivate,
            IsPageNotBlocked,
        ),
        'update': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
        ),
        'partial_update': (
            IsAuthenticated,
            IsPageOwner,
            IsPageNotBlocked,
        ),
        'destroy': (
            IsAuthenticated,
            IsPageOwnerOrAdminOrModerator,
            IsPageNotBlocked,
        ),
        'like': (
            IsAuthenticated,
            IsPageNotPrivate,
            IsPageNotBlocked
        ),
    }

    def get_queryset(self):
        parent_page_id = self.kwargs.get('parent_lookup_page_id')
        return Post.objects.get_posts_of_page(parent_page_id)

    def get_permissions(self):
        self.permission_classes = self.permission_map.get(self.action, [])
        return super(self.__class__, self).get_permissions()

    def create(self, request, *args, **kwargs):
        parent_page_id = self.kwargs.get('parent_lookup_page_id')
        posts_url = request.build_absolute_uri()
        send_notification_to_followers(parent_page_id, posts_url)
        return super().create(request, args, kwargs)

    def list(self, request, *args, **kwargs):
        parent_page_id = self.kwargs.get('parent_lookup_page_id')
        page = get_object_or_404(Page, pk=parent_page_id)
        self.check_object_permissions(request, page)
        return super().list(request, args, kwargs)

    @action(detail=True, methods=['patch'])
    def like(self, request, parent_lookup_page_id=None, pk=None):
        page = get_object_or_404(Page, pk=parent_lookup_page_id)
        post = get_object_or_404(Post, pk=pk)
        self.check_object_permissions(request, page)
        like_or_unlike_post(post, request.user)
        return Response('Success', status=status.HTTP_200_OK)


class UserPageFilter(generics.ListAPIView):
    acceptable_page_params = {'name', 'uuid', 'tags'}
    acceptable_user_params = {'username', 'first_name', 'last_name'}

    def get_queryset(self):
        params = {key: value for key, value in self.request.GET.items()}
        type = params.pop('type', None)

        if type == 'page' and set(params).issubset(self.acceptable_page_params):
            self.serializer_class = PageSerializer
            return Page.objects.filter(**params)
        elif type == 'user' and set(params).issubset(self.acceptable_user_params):
            self.serializer_class = UserSerializer
            return User.objects.filter(**params)
        else:
            raise InvalidFilterType()
