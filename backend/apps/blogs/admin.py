from django.contrib import admin

from .models import Blog


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ["id", "address", "name", "owner", "last_post_no", "deleted_at", "created_at"]
    search_fields = ["address", "name"]
