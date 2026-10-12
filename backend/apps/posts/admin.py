from django.contrib import admin

from .models import Category, Image, Post, Tag, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["sort_order", "name", "slug"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "blog", "name", "parent", "sort_order"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["id", "blog", "name"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["id", "blog", "post_no", "title", "status", "visibility", "published_at", "hidden_at"]
    list_filter = ["status", "visibility"]
    search_fields = ["title"]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "file", "uploader", "size_bytes", "created_at"]
