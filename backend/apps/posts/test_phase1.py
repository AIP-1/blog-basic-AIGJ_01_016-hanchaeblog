"""방 관리 · 마을에서 찾기 (API 명세서 4.4 · 4.8)."""

from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User
from apps.blogs.models import Blog

from .models import Category, Post, PostTag, Tag


def login(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class RoomTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("minju@example.com", "password123", nickname="민주")
        self.other = User.objects.create_user("seohyun@example.com", "password123", nickname="서현")
        self.blog = Blog.objects.create(owner=self.owner, address="minju", name="민주의 한채", last_post_no=2)
        self.dev = Category.objects.create(blog=self.blog, name="개발", sort_order=0)
        self.trip = Category.objects.create(blog=self.blog, name="여행", sort_order=1)
        for no in (1, 2):
            Post.objects.create(
                blog=self.blog, post_no=no, title=f"기록 {no}", content="<p>본문</p>", content_text="본문",
                status=Post.Status.PUBLISHED, published_at=timezone.now(), category=self.trip,
            )
        self.owner_client = login(self.owner)
        self.other_client = login(self.other)

    def test_rename(self):
        url = f"/api/blogs/minju/categories/{self.dev.pk}"
        self.assertEqual(self.other_client.patch(url, {"name": "코딩"}, format="json").status_code, 403)
        self.assertEqual(self.owner_client.patch(url, {"name": "여행"}, format="json").status_code, 409)
        res = self.owner_client.patch(url, {"name": "코딩"}, format="json")
        self.assertEqual((res.status_code, res.json()["name"]), (200, "코딩"))

    def test_delete_moves_posts_to_maru(self):
        res = self.owner_client.delete(f"/api/blogs/minju/categories/{self.trip.pk}")
        self.assertEqual(res.json(), {"moved_to_uncategorized": 2})
        rooms = self.owner_client.get("/api/blogs/minju/categories").json()
        self.assertEqual(([r["name"] for r in rooms["rooms"]], rooms["uncategorized_count"]), (["개발"], 2))

    def test_reorder(self):
        url = "/api/blogs/minju/categories/order"
        self.assertEqual(self.owner_client.put(url, {"ids": [self.trip.pk]}, format="json").status_code, 400)
        self.assertEqual(self.owner_client.put(url, {"ids": [self.trip.pk, self.trip.pk]}, format="json").status_code, 400)
        res = self.owner_client.put(url, {"ids": [self.trip.pk, self.dev.pk]}, format="json")
        self.assertEqual(res.status_code, 200)
        names = [r["name"] for r in self.owner_client.get("/api/blogs/minju/categories").json()["rooms"]]
        self.assertEqual(names, ["여행", "개발"])


class SearchTests(APITestCase):
    def setUp(self):
        owner = User.objects.create_user("minju@example.com", "password123", nickname="민주")
        self.blog = Blog.objects.create(owner=owner, address="minju", name="한옥에 사는 집", description="오래된 집")
        Blog.objects.create(
            owner=User.objects.create_user("jiwon@example.com", "password123", nickname="지원"),
            address="jiwon", name="지원의 한채", description="한옥 스테이 여행기",
        )
        self.in_body = self.post(1, "서촌 산책", "골목의 한옥 지붕")
        self.in_title = self.post(2, "경주 한옥 마을", "이틀 동안")
        self.in_tag = self.post(3, "처마 이야기", "빗물")
        PostTag.objects.create(post=self.in_tag, tag=Tag.objects.create(blog=self.blog, name="한옥"))
        self.post(4, "한옥 비밀 메모", "나만", Post.Visibility.PRIVATE)
        self.guest = APIClient()

    def post(self, no, title, text, visibility=Post.Visibility.PUBLIC):
        return Post.objects.create(
            blog=self.blog, post_no=no, title=title, content=f"<p>{text}</p>", content_text=text,
            status=Post.Status.PUBLISHED, published_at=timezone.now(), visibility=visibility,
        )

    def test_posts_relevance_and_latest(self):
        res = self.guest.get("/api/search/posts", {"q": "한옥"}).json()
        self.assertEqual([p["no"] for p in res["items"]], [2, 3, 1])  # 제목 > 태그 > 본문, 나만 보기 빠짐
        latest = self.guest.get("/api/search/posts", {"q": "한옥", "sort": "latest"}).json()
        self.assertEqual([p["no"] for p in latest["items"]], [3, 2, 1])
        self.assertEqual(self.guest.get("/api/search/posts", {"q": " "}).status_code, 400)

    def test_blogs_name_first(self):
        res = self.guest.get("/api/search/blogs", {"q": "한옥"}).json()
        self.assertEqual([b["address"] for b in res["items"]], ["minju", "jiwon"])
