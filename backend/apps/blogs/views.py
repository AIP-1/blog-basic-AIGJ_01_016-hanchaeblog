"""한채 API (API 명세서 4.2, 기능 BLOG-01 · BLOG-02 · SUB-03)."""

from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.access import get_visible_blog_or_404, visible_posts
from apps.common.errors import APIError
from apps.common.permissions import IsMember
from apps.community.models import Subscription
from apps.posts.images import get_own_image

from .models import Blog
from .serializers import BlogCreateSerializer, BlogUpdateSerializer, blog_summary, check_address


def blog_detail(blog, request):
    viewer = request.user
    data = blog_summary(blog, request)
    data["post_count"] = visible_posts(viewer).filter(blog=blog).count()
    data["is_owner"] = viewer.is_authenticated and blog.owner_id == viewer.pk
    data["is_subscribed"] = (
        viewer.is_authenticated and Subscription.objects.filter(blog=blog, subscriber=viewer).exists()
    )
    return data


class AddressAvailableView(APIView):
    """GET /api/blogs/address-available?address= — 한채 주소를 쓸 수 있는지."""

    permission_classes = [IsMember]

    def get(self, request):
        problem = check_address(request.query_params.get("address", "").strip())
        return Response({"available": problem is None, "reason": problem})


class BlogCreateView(APIView):
    """POST /api/blogs — 한채 짓기. 회원당 살아 있는 한채는 하나 (BLOG-01)."""

    permission_classes = [IsMember]

    def post(self, request):
        if Blog.objects.filter(owner=request.user, deleted_at__isnull=True).exists():
            raise APIError(409, "CONFLICT", "이미 지은 한채가 있어요. 한 사람은 한 채만 지을 수 있어요.")
        serializer = BlogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                blog = Blog.objects.create(owner=request.user, **serializer.validated_data)
        except IntegrityError:
            # 동시에 두 번 눌렀거나, 그 사이 같은 주소를 누가 먼저 가져갔다
            if Blog.objects.filter(owner=request.user, deleted_at__isnull=True).exists():
                raise APIError(409, "CONFLICT", "이미 지은 한채가 있어요. 한 사람은 한 채만 지을 수 있어요.")
            raise APIError(409, "CONFLICT", "이미 있거나 예약된 주소예요.", fields={"address": "이미 있거나 예약된 주소예요."})
        return Response(blog_detail(blog, request), status=status.HTTP_201_CREATED)


class BlogDetailView(APIView):
    """GET · PATCH /api/blogs/{address} — 대문 정보 보기 · 한채 관리 (BLOG-02)."""

    def get(self, request, address):
        blog = get_visible_blog_or_404(address, request.user)
        return Response(blog_detail(blog, request))

    def patch(self, request, address):
        if not request.user.is_authenticated:
            raise APIError(401, "AUTH_REQUIRED", "로그인이 필요해요.")
        blog = get_visible_blog_or_404(address, request.user)
        if blog.owner_id != request.user.pk:
            raise APIError(403, "FORBIDDEN", "이 한채의 주인만 바꿀 수 있어요.")
        serializer = BlogUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        for field in ("name", "description"):
            if field in data:
                setattr(blog, field, data[field])
        if "profile_image_id" in data:
            image_id = data["profile_image_id"]
            blog.profile_image = get_own_image(image_id, request.user).file.name if image_id is not None else None
        blog.save()
        return Response(blog_detail(blog, request))
