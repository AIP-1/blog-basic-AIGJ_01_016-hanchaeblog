"""회원 · 로그인 API (API 명세서 4.1, 기능 AUTH-01 ~ AUTH-05)."""

import logging
import smtplib

from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.access import current_sanction
from apps.common.errors import APIError
from apps.common.permissions import EnforceCsrfMixin, IsMember
from apps.posts.images import get_own_image

from .models import User
from .serializers import LoginSerializer, MeUpdateSerializer, NicknameField, SignupSerializer, me_payload

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """GET /api/auth/csrf — CSRF 쿠키를 준다. 앱을 열 때 한 번 부른다."""

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me — 지금 로그인한 사람. 비회원이면 {"user": null}."""

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"user": None})
        return Response({"user": me_payload(request.user, request)})


class SignupView(EnforceCsrfMixin, APIView):
    """POST /api/auth/signup — 이메일 가입. 인증 메일을 보낸다 (AUTH-01)."""

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        conflicts = {}
        if User.objects.filter(email=data["email"]).exists():
            conflicts["email"] = "이미 가입한 이메일이에요."
        if User.objects.filter(nickname=data["nickname"]).exists():
            conflicts["nickname"] = "이미 쓰고 있는 닉네임이에요."
        if conflicts:
            raise APIError(409, "CONFLICT", "이미 쓰고 있는 값이 있어요.", fields=conflicts)

        now = timezone.now()
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    data["email"],
                    data["password"],
                    nickname=data["nickname"],
                    terms_agreed_at=now,
                    privacy_agreed_at=now,
                )
                address = EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=False)
                # 메일을 못 보내면 가입도 되돌린다. 남겨 두면 메일 없이 '이미 가입한 이메일'만 남는다
                address.send_confirmation(request, signup=True)
        except IntegrityError:
            raise APIError(409, "CONFLICT", "이미 쓰고 있는 값이 있어요.")
        except (smtplib.SMTPException, OSError):
            logger.exception("인증 메일을 보내지 못했어요")
            raise APIError(503, "MAIL_FAILED", "인증 메일을 보내지 못했어요. 잠시 뒤 다시 가입해 주세요.")
        return Response({"email_verification_sent": True}, status=status.HTTP_201_CREATED)


class EmailVerifyView(EnforceCsrfMixin, APIView):
    """POST /api/auth/email/verify — 인증 메일의 키로 이메일을 인증한다."""

    def post(self, request):
        key = str(request.data.get("key", "")).strip()
        confirmation = EmailConfirmationHMAC.from_key(key) if key else None
        if confirmation is None or confirmation.confirm(request) is None:
            raise APIError(
                400, "VALIDATION_ERROR", "인증 링크가 만료됐거나 잘못됐어요.", fields={"key": "메일을 다시 받아 주세요."}
            )
        return Response({"verified": True})


class LoginView(EnforceCsrfMixin, APIView):
    """POST /api/auth/login — 이메일 로그인 (AUTH-01)."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = authenticate(request, username=email, password=serializer.validated_data["password"])
        if user is None:
            raise APIError(401, "LOGIN_FAILED", "이메일이나 비밀번호가 맞지 않아요.")

        addresses = EmailAddress.objects.filter(user=user)
        if addresses.exists() and not addresses.filter(verified=True).exists():
            raise APIError(403, "EMAIL_NOT_VERIFIED", "메일함에서 이메일 인증을 먼저 마쳐 주세요.")

        sanction = current_sanction(user)
        if sanction is not None:
            raise APIError(
                403,
                "SUSPENDED",
                "이용이 제한된 계정이에요.",
                detail={"reason": sanction.reason, "ends_at": sanction.ends_at},
            )

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response({"user": me_payload(user, request)})


class LogoutView(APIView):
    """POST /api/auth/logout (AUTH-02)."""

    permission_classes = [IsMember]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NicknameAvailableView(APIView):
    """GET /api/auth/nickname-available?nickname= — 닉네임을 쓸 수 있는지 (AUTH-05)."""

    def get(self, request):
        field = NicknameField()
        try:
            nickname = field.run_validation(request.query_params.get("nickname", ""))
        except Exception:
            return Response({"available": False, "reason": "INVALID"})
        taken = User.objects.filter(nickname=nickname)
        if request.user.is_authenticated:
            taken = taken.exclude(pk=request.user.pk)
        if taken.exists():
            return Response({"available": False, "reason": "TAKEN"})
        return Response({"available": True, "reason": None})


class MeUpdateView(APIView):
    """PATCH /api/me — 닉네임 · 프로필 이미지 수정 (AUTH-05)."""

    permission_classes = [IsMember]

    def patch(self, request):
        serializer = MeUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        if "nickname" in data:
            user.nickname = data["nickname"]
        if "profile_image_id" in data:
            image_id = data["profile_image_id"]
            user.profile_image = get_own_image(image_id, user).file.name if image_id is not None else None
        try:
            user.save()
        except IntegrityError:
            raise APIError(409, "CONFLICT", "이미 쓰고 있는 닉네임이에요.", fields={"nickname": "이미 쓰고 있는 닉네임이에요."})
        return Response({"user": me_payload(user, request)})
