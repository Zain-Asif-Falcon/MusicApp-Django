from rest_framework import permissions


class ArtistOnly(permissions.BasePermission):
    message = "You are not an artist!"

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.user_type == "artist")
