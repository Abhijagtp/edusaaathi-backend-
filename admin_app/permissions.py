from rest_framework import permissions

class IsConsultant(permissions.BasePermission):
    """
    Allows access to authenticated consultants, counselors, staff, and superusers.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (
            user.role in ['CONSULTANT', 'COUNSELOR', 'ADMIN', 'STAFF'] or
            user.is_staff or
            user.is_superuser
        )


class IsAdminOrStaff(permissions.BasePermission):
    """
    Allows access only to admin or staff members.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (
            user.role in ['ADMIN', 'STAFF'] or
            user.is_staff or
            user.is_superuser
        )
