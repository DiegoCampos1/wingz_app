"""Custom DRF permissions for the accounts/auth layer."""

from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow access only to authenticated users whose role is 'admin'.

    Anonymous requests are rejected (401 via authentication), authenticated
    non-admin users are denied (403).
    """

    message = "Only admin users may access this resource."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)
