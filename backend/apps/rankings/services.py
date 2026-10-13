"""정각 순위 계산 (API 명세서 4.9, 기능명세서 9.2).

학교 서버에는 정각마다 도는 작업을 따로 둘 수 없어서, 그 시간의 첫 요청이 직전 정각 기준으로
계산해 저장한다. 다음 정각까지는 저장한 값을 그대로 준다. 결과는 '매 정각 계산'과 같다.
"""

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone

from apps.common.access import visible_blogs
from apps.posts.models import Post, PostView

from .models import RankingEntry, RankingSnapshot

POST_LIMIT = 10
BLOG_LIMIT = 10
KEEP = timedelta(days=2)


def current_window_end(now=None):
    now = timezone.localtime(now or timezone.now())
    return now.replace(minute=0, second=0, microsecond=0)


def ranked_views(window_end, hours):
    """구간 안의 조회 기록. 공개 기록 · 보이는 한채만 센다."""
    return PostView.objects.filter(
        viewed_at__gte=window_end - timedelta(hours=hours),
        viewed_at__lt=window_end,
        post__status=Post.Status.PUBLISHED,
        post__visibility=Post.Visibility.PUBLIC,
        post__hidden_at__isnull=True,
        post__blog__in=visible_blogs(),
    )


def pick_window(window_end):
    """1시간 조회가 있으면 1H, 없으면 24H, 그것도 없으면 EMPTY."""
    for hours, basis in ((1, RankingSnapshot.Basis.ONE_HOUR), (24, RankingSnapshot.Basis.ONE_DAY)):
        views = ranked_views(window_end, hours)
        if views.exists():
            return basis, views
    return RankingSnapshot.Basis.EMPTY, None


def build(kind, window_end):
    basis, views = pick_window(window_end)
    entries = []
    if views is not None:
        if kind == RankingSnapshot.Kind.POST:
            rows = views.values("post").annotate(n=Count("id")).order_by("-n", "post")[:POST_LIMIT]
            entries = [RankingEntry(post_id=r["post"], position=i + 1, score=r["n"]) for i, r in enumerate(rows)]
        else:
            rows = views.values("post__blog").annotate(n=Count("id")).order_by("-n", "post__blog")[:BLOG_LIMIT]
            entries = [RankingEntry(blog_id=r["post__blog"], position=i + 1, score=r["n"]) for i, r in enumerate(rows)]
    snapshot = RankingSnapshot.objects.create(kind=kind, window_end=window_end, basis=basis)
    for entry in entries:
        entry.snapshot = snapshot
    RankingEntry.objects.bulk_create(entries)
    return snapshot


def snapshot_for(kind, now=None):
    """이번 정각의 스냅숏. 없으면 만든다 (동시에 두 요청이 와도 하나만 남는다)."""
    window_end = current_window_end(now)
    snapshot = RankingSnapshot.objects.filter(kind=kind, window_end=window_end).first()
    if snapshot:
        return snapshot
    try:
        with transaction.atomic():
            snapshot = build(kind, window_end)
    except IntegrityError:
        return RankingSnapshot.objects.get(kind=kind, window_end=window_end)
    RankingSnapshot.objects.filter(kind=kind, window_end__lt=window_end - KEEP).delete()
    return snapshot
