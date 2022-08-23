from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions
from user.models import User


class IsUserOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.Roles.ADMIN


class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.Roles.MODERATOR


class IsAdminOrModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return IsAdmin.has_permission(self, request, view) or \
            IsModerator.has_permission(self, request, view)


class IsUserOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return IsAdmin.has_permission(self, request, view) or \
            IsUserOwner.has_object_permission(self, request, view, obj)
