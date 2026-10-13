"""순위 API (API 명세서 4.9): 지금 많이 읽는 기록 · 북적이는 한채."""

from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blogs.serializers import blog_summary
from apps.common.access import visible_blogs
from apps.posts.serializers import post_summary, with_counts
from apps.posts.views import public_feed

from .models import RankingSnapshot
from .services import ranked_views, snapshot_for


def limit_param(request, default=10):
    try:
        return min(10, max(1, int(request.query_params.get("limit", default))))
    except ValueError:
        return default


class PostRankingView(APIView):
    """GET /api/rankings/posts?limit= — 지금 많이 읽는 기록 (HOME-02)."""

    def get(self, request):
        snapshot = snapshot_for(RankingSnapshot.Kind.POST)
        entries = list(snapshot.entries.all())
        # 그 사이 숨기거나 나만 보기로 바꾼 기록은 응답할 때 뺀다
        posts = {p.pk: p for p in with_counts(public_feed(request.user).filter(pk__in=[e.post_id for e in entries]))}
        items = [
            {"position": e.position, "score": e.score, "post": post_summary(posts[e.post_id], request)}
            for e in entries
            if e.post_id in posts
        ][: limit_param(request)]
        return Response({"window_end": snapshot.window_end, "basis": snapshot.basis, "items": items})


class BlogRankingView(APIView):
    """GET /api/rankings/blogs?limit= — 북적이는 한채, 대표 기록과 함께 (HOME-04)."""

    def get(self, request):
        snapshot = snapshot_for(RankingSnapshot.Kind.BLOGGER)
        entries = list(snapshot.entries.all())
        blogs = {b.pk: b for b in visible_blogs().filter(pk__in=[e.blog_id for e in entries]).select_related("owner")}
        hours = 1 if snapshot.basis == RankingSnapshot.Basis.ONE_HOUR else 24
        items = []
        for e in entries:
            blog = blogs.get(e.blog_id)
            if blog is None:
                continue
            top = (
                ranked_views(snapshot.window_end, hours)
                .filter(post__blog=blog)
                .values("post__post_no", "post__title")
                .order_by()
            )
            top = top.annotate(n=Count("id")).order_by("-n", "post__post_no").first()
            items.append(
                {
                    "position": e.position,
                    "score": e.score,
                    "blog": blog_summary(blog, request),
                    "top_post": {"no": top["post__post_no"], "title": top["post__title"]} if top else None,
                }
            )
        return Response({"window_end": snapshot.window_end, "basis": snapshot.basis, "items": items[: limit_param(request)]})
