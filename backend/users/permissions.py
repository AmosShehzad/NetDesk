from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Allows access only to users with role=CUSTOMER."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'CUSTOMER'


class IsSupportAgent(BasePermission):
    """Allows access only to Support Agents."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SUPPORT_AGENT'


class IsManagerOrAdmin(BasePermission):
    """Allows access to Managers and Admins (elevated roles)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['MANAGER', 'ADMIN']


class IsTechnician(BasePermission):
    """Allows access only to Technicians."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'TECHNICIAN'


class IsStaffRole(BasePermission):
    """
    Allows Support Agent, Technician, Manager, or Admin.
    Used to block Customers from an entire endpoint, not just filter their data.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            'SUPPORT_AGENT', 'TECHNICIAN', 'MANAGER', 'ADMIN'
        ]