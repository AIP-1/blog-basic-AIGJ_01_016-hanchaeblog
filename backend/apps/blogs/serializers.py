import re

from rest_framework import serializers

from apps.accounts.serializers import absolute_url, user_summary

from .models import Blog

ADDRESS_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{2,30})[a-z0-9]$")

# 한채 주소로 쓸 수 없는 서비스 예약어 (API 명세서 4.2, 7.2)
RESERVED_ADDRESSES = {
    "www", "api", "admin", "django-admin", "login", "logout", "signup", "accounts", "account",
    "static", "media", "mail", "email", "help", "about", "search", "topic", "topics", "ranking",
    "me", "new", "build", "manage", "blog", "blogs", "hanchae", "root", "support", "dev", "test",
    "village", "notice", "terms", "privacy", "address-available",
}


def check_address(address):
    """한채 주소를 쓸 수 있으면 None, 아니면 INVALID · RESERVED · TAKEN."""
    if not ADDRESS_RE.match(address or ""):
        return "INVALID"
    if address in RESERVED_ADDRESSES:
        return "RESERVED"
    if Blog.objects.filter(address=address).exists():  # 허문 한채의 주소도 영구 예약
        return "TAKEN"
    return None


ADDRESS_MESSAGES = {
    "INVALID": "한채 주소는 영문 소문자 · 숫자 · 하이픈 4~32자이고, 하이픈으로 시작하거나 끝날 수 없어요.",
    "RESERVED": "서비스가 쓰는 주소라 쓸 수 없어요.",
    "TAKEN": "이미 있거나 예약된 주소예요.",
}


def blog_summary(blog, request):
    """BlogSummary (API 명세서 3.2)."""
    return {
        "address": blog.address,
        "name": blog.name,
        "description": blog.description,
        "profile_image_url": absolute_url(request, blog.profile_image),
        "owner": user_summary(blog.owner, request),
        "subscriber_count": blog.subscriptions.count(),
    }


class BlogCreateSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=32, trim_whitespace=True)
    name = serializers.CharField(max_length=40, trim_whitespace=True, error_messages={"blank": "한채 이름을 써 주세요."})
    description = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate_address(self, value):
        problem = check_address(value)
        if problem:
            raise serializers.ValidationError(ADDRESS_MESSAGES[problem])
        return value


class BlogUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=40, trim_whitespace=True, required=False, error_messages={"blank": "한채 이름을 써 주세요."})
    description = serializers.CharField(max_length=200, required=False, allow_blank=True)
    profile_image_id = serializers.IntegerField(required=False, allow_null=True)
