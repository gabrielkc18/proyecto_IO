class SuperuserOnlyAdminMixin:
    def _is_platform_operator(self, request):
        return (
            request.user.is_authenticated
            and request.user.is_active
            and request.user.is_superuser
        )

    def has_module_permission(self, request):
        return self._is_platform_operator(request)

    def has_view_permission(self, request, obj=None):
        return self._is_platform_operator(request)

    def has_add_permission(self, request):
        return self._is_platform_operator(request)

    def has_change_permission(self, request, obj=None):
        return self._is_platform_operator(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_platform_operator(request)


class ReadOnlyRecordsAdminMixin(SuperuserOnlyAdminMixin):
    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
