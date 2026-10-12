"""누가 무엇을 볼 수 있는지 (통합 명세 3장 · 4.1, API 명세서 2.3).

볼 수 없는 것은 모두 404 로 답해 있다는 사실도 숨긴다.
"""

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.moderation.models import UserSanction


def active_sanctions():
    now = timezone.now()
    return UserSanction.objects.filter(released_at__isnull=True, starts_at__lte=now).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    )


def current_sanction(user):
    """지금 걸려 있는 이용 제한. 없으면 None."""
    if not user or not user.pk:
        return None
    return active_sanctions().filter(user=user).order_by("-starts_at").first()


def visible_blogs(queryset=None):
    """다른 사람에게 보이는 한채: 허물지 않았고, 주인이 이용 제한 중이 아니다 (ERD REQ-012)."""
    from apps.blogs.models import Blog

    qs = queryset if queryset is not None else Blog.objects.all()
    return qs.filter(deleted_at__isnull=True).exclude(
        Exists(active_sanctions().filter(user=OuterRef("owner")))
    )


def get_visible_blog_or_404(address, viewer=None):
    """주소로 한채를 찾는다. 주인 본인은 이용 제한 중이어도 자기 한채를 볼 수 있다."""
    from rest_framework.exceptions import NotFound

    from apps.blogs.models import Blog

    blog = Blog.objects.select_related("owner").filter(address=address, deleted_at__isnull=True).first()
    if blog is None:
        raise NotFound()
    is_owner = viewer is not None and viewer.is_authenticated and blog.owner_id == viewer.pk
    if not is_owner and current_sanction(blog.owner) is not None:
        raise NotFound()
    return blog


def visible_posts(viewer, queryset=None):
    """보는 사람이 볼 수 있는 발행된 기록 (통합 명세 4.1).

    - 관리자가 숨긴 기록은 빠진다(주인에게는 보인다).
    - 공개 기록은 누구나, 이웃 공개는 그 한채의 이웃과 주인만, 나만 보기는 주인만.
    """
    from apps.posts.models import Post

    qs = queryset if queryset is not None else Post.objects.all()
    qs = qs.filter(status=Post.Status.PUBLISHED)
    if viewer is None or not viewer.is_authenticated:
        return qs.filter(visibility=Post.Visibility.PUBLIC, hidden_at__isnull=True)

    from apps.community.models import Subscription

    is_owner = Q(blog__owner=viewer)
    is_neighbor = Exists(Subscription.objects.filter(blog=OuterRef("blog"), subscriber=viewer))
    can_see = (
        Q(visibility=Post.Visibility.PUBLIC)
        | (Q(visibility=Post.Visibility.SUBSCRIBERS) & (is_owner | is_neighbor))
        | (Q(visibility=Post.Visibility.PRIVATE) & is_owner)
    )
    return qs.filter(can_see).filter(Q(hidden_at__isnull=True) | is_owner)
