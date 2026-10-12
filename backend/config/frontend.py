"""
화면 파일(index.html · css · js · assets)을 Django 가 함께 내보낸다.

화면과 API 를 같은 주소에서 띄워야 세션 쿠키 · CSRF 가 그대로 통한다.
저장소 루트에는 backend/.env 같은 파일도 있으므로, 화면에 필요한 것만 내보낸다.
"""

from django.conf import settings
from django.http import Http404
from django.views.static import serve

# 루트의 *.html 과 이 폴더들 안의 파일만 내보낸다
FRONTEND_FOLDERS = {"css", "js", "assets"}


def frontend(request, path=""):
    path = path or "index.html"
    top, _, rest = path.partition("/")
    if rest:
        allowed = top in FRONTEND_FOLDERS
    else:
        # /login 처럼 확장자 없는 주소는 같은 이름의 .html 화면으로
        if "." not in path and (settings.FRONTEND_DIR / f"{path}.html").is_file():
            path = f"{path}.html"
        allowed = path.endswith(".html")
    if not allowed:
        raise Http404
    return serve(request, path, document_root=settings.FRONTEND_DIR)
