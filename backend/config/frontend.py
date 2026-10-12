"""
화면 파일(index.html · css · js · assets)을 Django 가 함께 내보낸다.

화면과 API 를 같은 주소에서 띄워야 세션 쿠키 · CSRF 가 그대로 통한다.
저장소 루트에는 backend/.env 같은 파일도 있으므로, 화면에 필요한 것만 내보낸다.
"""

import posixpath

from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.views.static import serve

# 루트의 *.html 과 이 폴더들 안의 파일만 내보낸다
FRONTEND_FOLDERS = {"css", "js", "assets"}


def frontend(request, path=""):
    # css/../backend/.env 처럼 폴더 밖으로 나가는 주소를 막는다. 정리한 뒤의 경로로 다시 검사한다
    if "\\" in path or ".." in path.split("/"):
        raise Http404
    # /login/ 처럼 끝에 / 가 붙으면 /login 으로 보낸다 (화면의 css/… 같은 상대 주소가 어긋나지 않게)
    if path.endswith("/") and path.strip("/"):
        query = request.META.get("QUERY_STRING", "")
        return HttpResponsePermanentRedirect("/" + path.strip("/") + (f"?{query}" if query else ""))
    path = posixpath.normpath(path).lstrip("/") if path else ""
    if path in ("", "."):
        path = "index.html"
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
