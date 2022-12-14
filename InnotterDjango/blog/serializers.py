from blog.models import Tag, Page, Post
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    pages = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'pages'
        )
        read_only_fields = (
            'id',
            'pages'
        )


class PageSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    posts = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta:
        model = Page
        fields = (
            'id',
            'name',
            'uuid',
            'description',
            'tags',
            'owner',
            'image',
            'is_private',
            'followers',
            'follow_requests',
            'unblock_date',
            'posts'
        )
        read_only_fields = (
            'id',
            'followers',
            'follow_requests',
            'unblock_date',
            'posts',
        )


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'page',
            'content',
            'reply_to',
            'created_at',
            'updated_at',
            'users_liked'
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'users_liked'
        )
