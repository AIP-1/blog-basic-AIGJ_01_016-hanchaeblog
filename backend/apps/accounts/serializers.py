from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


def absolute_url(request, field_file):
    """올린 파일의 주소. 호스트 없이 /media/... 로 준다 (도메인 · https 가 바뀌어도 깨지지 않게)."""
    return field_file.url if field_file else None


def alive_blog_address(user):
    blog = user.blogs.filter(deleted_at__isnull=True).only("address").first()
    return blog.address if blog else None


def user_summary(user, request):
    """UserSummary (API 명세서 3.1). 탈퇴한 회원은 '떠난 사람'."""
    if user is None or not user.is_active:
        return {"nickname": None, "profile_image_url": None, "blog_address": None, "withdrawn": True}
    return {
        "nickname": user.nickname,
        "profile_image_url": absolute_url(request, user.profile_image),
        "blog_address": alive_blog_address(user),
    }


def me_payload(user, request):
    """GET /api/auth/me 의 user (API 명세서 4.1)."""
    return {
        "nickname": user.nickname,
        "email": user.email,
        "profile_image_url": absolute_url(request, user.profile_image),
        "role": user.role,
        "blog_address": alive_blog_address(user),
    }


class NicknameField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(min_length=2, max_length=20, trim_whitespace=True, **kwargs)
        self.error_messages.update(
            {
                "min_length": "닉네임은 2~20자로 써 주세요.",
                "max_length": "닉네임은 2~20자로 써 주세요.",
                "blank": "닉네임을 써 주세요.",
                "required": "닉네임을 써 주세요.",
            }
        )


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254, error_messages={"invalid": "이메일 형식을 확인해 주세요."})
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    nickname = NicknameField()
    agree_terms = serializers.BooleanField()
    agree_privacy = serializers.BooleanField()
    over_14 = serializers.BooleanField()

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError:
            raise serializers.ValidationError("비밀번호는 8자 이상으로 써 주세요.")
        return value

    def validate_agree_terms(self, value):
        if not value:
            raise serializers.ValidationError("이용약관에 동의해야 가입할 수 있어요.")
        return value

    def validate_agree_privacy(self, value):
        if not value:
            raise serializers.ValidationError("개인정보 수집 · 이용에 동의해야 가입할 수 있어요.")
        return value

    def validate_over_14(self, value):
        if not value:
            raise serializers.ValidationError("만 14세 이상만 가입할 수 있어요.")
        return value


class EmailResendSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=254, error_messages={"invalid": "이메일 형식을 확인해 주세요.", "required": "이메일을 써 주세요."}
    )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class MeUpdateSerializer(serializers.Serializer):
    nickname = NicknameField(required=False)
    profile_image_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_nickname(self, value):
        user = self.context["request"].user
        if User.objects.filter(nickname=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("이미 쓰고 있는 닉네임이에요.")
        return value
