from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow only authenticated users whose role is ADMIN."""

    message = 'Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, 'role', None) == 'ADMIN'
        )
