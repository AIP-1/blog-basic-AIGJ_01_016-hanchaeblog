"""순위 (API 명세서 4.9)."""

from datetime import timedelta
from unittest import mock

from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User
from apps.blogs.models import Blog
from apps.posts.models import Post, PostView

from .models import RankingSnapshot
from .services import current_window_end


class RankingTests(APITestCase):
    def setUp(self):
        self.end = current_window_end()
        owner = User.objects.create_user("minju@example.com", "password123", nickname="민주")
        other = User.objects.create_user("jiwon@example.com", "password123", nickname="지원")
        self.minju = Blog.objects.create(owner=owner, address="minju", name="민주의 한채")
        self.jiwon = Blog.objects.create(owner=other, address="jiwon", name="지원의 한채")
        self.a = self.post(self.minju, 1, "많이 읽힌 기록")
        self.b = self.post(self.jiwon, 1, "조금 읽힌 기록")
        self.guest = APIClient()

    def post(self, blog, no, title):
        return Post.objects.create(
            blog=blog, post_no=no, title=title, content="<p>본문</p>", content_text="본문",
            status=Post.Status.PUBLISHED, published_at=timezone.now() - timedelta(days=1),
        )

    def view(self, post, minutes_ago, n=1):
        for i in range(n):
            PostView.objects.create(post=post, viewer_key=f"{post.pk}-{minutes_ago}-{i}", viewed_at=self.end - timedelta(minutes=minutes_ago))

    def test_empty(self):
        res = self.guest.get("/api/rankings/posts").json()
        self.assertEqual((res["basis"], res["items"]), ("EMPTY", []))

    def test_one_hour_and_blogs(self):
        self.view(self.a, 10, n=3)
        self.view(self.b, 20, n=1)
        self.view(self.b, 300, n=9)  # 1시간 밖: 1H 기준에는 안 센다
        res = self.guest.get("/api/rankings/posts").json()
        self.assertEqual(res["basis"], "1H")
        self.assertEqual([(i["position"], i["score"], i["post"]["title"]) for i in res["items"]], [(1, 3, "많이 읽힌 기록"), (2, 1, "조금 읽힌 기록")])
        blogs = self.guest.get("/api/rankings/blogs").json()
        self.assertEqual(blogs["items"][0]["blog"]["address"], "minju")
        self.assertEqual(blogs["items"][0]["top_post"], {"no": 1, "title": "많이 읽힌 기록"})

    def test_falls_back_to_24h_and_keeps_snapshot_until_next_hour(self):
        self.view(self.b, 300, n=2)
        self.assertEqual(self.guest.get("/api/rankings/posts").json()["basis"], "24H")
        self.view(self.a, 10, n=5)  # 같은 정각 안에서는 저장한 순위 그대로
        self.assertEqual(self.guest.get("/api/rankings/posts").json()["basis"], "24H")
        self.assertEqual(RankingSnapshot.objects.filter(kind="POST").count(), 1)
        with mock.patch("apps.rankings.services.timezone.now", return_value=self.end + timedelta(hours=1, minutes=5)):
            self.assertEqual(self.guest.get("/api/rankings/posts").json()["items"][0]["post"]["title"], "많이 읽힌 기록")

    def test_private_post_dropped_at_response(self):
        self.view(self.a, 10, n=3)
        self.guest.get("/api/rankings/posts")
        Post.objects.filter(pk=self.a.pk).update(visibility=Post.Visibility.PRIVATE)
        self.assertEqual(self.guest.get("/api/rankings/posts").json()["items"], [])
