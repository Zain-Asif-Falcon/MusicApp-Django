from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()
from users.models import Fan

admin.site.register(Fan)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "account_type", "uid")
    list_filter = ('is_staff', 'is_active', 'account_type')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                    'user_type',
                    'account_type',
                ),
            },
        ),
        (
            'Important dates',
            {
                'fields': (
                    'last_login',
                    'date_joined',
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'is_staff',
                    'is_active',
                    'is_superuser',
                ),
            },
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
