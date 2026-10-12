from rest_framework.permissions import BasePermission


class IsMember(BasePermission):
    """로그인한 회원 (API 명세서 2.3 '회원'). 없으면 401 AUTH_REQUIRED."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsServiceAdmin(BasePermission):
    """서비스 관리자(role = ADMIN). 비회원 401, 일반 회원 403."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "ADMIN")


class EnforceCsrfMixin:
    """로그인 전(비회원) 요청에도 CSRF 검사를 한다 (API 명세서 2.2).

    DRF 의 세션 인증은 로그인한 요청에만 CSRF 를 검사하므로, 가입 · 로그인처럼 비회원이 보내는
    바꾸는 요청에는 이 믹스인으로 같은 검사를 한다.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            from rest_framework.authentication import SessionAuthentication

            SessionAuthentication().enforce_csrf(request)
