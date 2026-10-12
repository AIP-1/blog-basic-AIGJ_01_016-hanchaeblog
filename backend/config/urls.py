from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from config.frontend import frontend

api_patterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.blogs.urls")),
    path("", include("apps.posts.urls")),
    path("", include("apps.community.urls")),
]

urlpatterns = [
    path("api/", include(api_patterns)),
    path("django-admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

# 나머지 주소는 화면 파일. 위의 주소(끝 / 를 빠뜨린 경우 포함)는 가리지 않는다
urlpatterns += [re_path(r"^(?!api/|django-admin|accounts|media/)(?P<path>.*)$", frontend)]
