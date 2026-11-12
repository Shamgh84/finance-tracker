from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnlyDefault(BasePermission):
    """دسته‌های پیش‌فرض فقط خواندنی‌اند؛ دسته‌های شخصی فقط توسط صاحبشان قابل تغییرند."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id