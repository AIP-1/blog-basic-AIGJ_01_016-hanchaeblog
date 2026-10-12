from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

api_patterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.blogs.urls")),
    path("", include("apps.posts.urls")),
]

urlpatterns = [
    path("api/", include(api_patterns)),
    path("django-admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
