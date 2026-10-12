from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
