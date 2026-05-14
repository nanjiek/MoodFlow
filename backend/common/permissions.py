from __future__ import annotations

from typing import Iterable

from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_roles(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    roles: set[str] = set()
    role = getattr(user, "role", None)
    if role:
        roles.add(str(role))

    if hasattr(user, "groups"):
        roles.update(user.groups.values_list("name", flat=True))

    return roles


def has_any_role(user, roles: Iterable[str]) -> bool:
    required_roles = {str(role) for role in roles}
    return bool(user_roles(user) & required_roles)


class HasAnyRole(BasePermission):
    required_roles: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        roles = getattr(view, "required_roles", self.required_roles)
        return has_any_role(request.user, roles)


class IsOwnerOrReadOnly(BasePermission):
    owner_field = "user"

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True

        owner_field = getattr(view, "owner_field", self.owner_field)
        owner = getattr(obj, owner_field, None)
        return owner == request.user
