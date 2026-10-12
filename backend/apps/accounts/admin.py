from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "nickname", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "nickname"]
    exclude = ["password", "groups", "user_permissions"]
