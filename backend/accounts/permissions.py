from rest_framework.permissions import BasePermission
class RolePermission(BasePermission):
    allowed_roles=()
    def has_permission(self,request,view):
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)
class IsAdmin(RolePermission): allowed_roles=("ADMIN",)
class IsFaculty(RolePermission): allowed_roles=("FACULTY",)
class IsFacultyOrAdmin(RolePermission): allowed_roles=("FACULTY","ADMIN")
class IsStudent(RolePermission): allowed_roles=("STUDENT",)
