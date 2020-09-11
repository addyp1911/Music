from rest_framework import permissions


class IsSuperAdminOrStaff(permissions.BasePermission):
    """
    A custom class to check if user is admin or staff
    """
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser


class IsOwnerAttributes(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user.uid == request.user.uid


class BaseViewSetPermissionMixin:
    def get_permissions(self):
        if self.action == 'list':
            permission_class = [
                permissions.IsAuthenticated
            ]
        elif self.action == 'destroy':
            permission_class = (permissions.IsAuthenticated, IsOwnerAttributes, )
        else:
            permission_class = [
                IsOwnerAttributes,
            ]
        return [permission() for permission in permission_class]
