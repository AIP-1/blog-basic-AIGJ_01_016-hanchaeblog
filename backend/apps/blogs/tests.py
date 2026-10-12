from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User

from .models import Blog


class OneHouseRuleTests(TestCase):
    """회원당 살아 있는 한채는 하나 (ERD REQ-003, 기능명세서 선택 7.2)."""

    def setUp(self):
        self.minju = User.objects.create_user("minju@example.com", "password123", nickname="민주")

    def test_second_live_blog_is_rejected(self):
        Blog.objects.create(owner=self.minju, address="minju", name="민주의 한채")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Blog.objects.create(owner=self.minju, address="minju-2", name="두 번째 집")

    def test_can_build_again_after_tearing_down(self):
        old = Blog.objects.create(owner=self.minju, address="minju", name="민주의 한채")
        old.deleted_at = timezone.now()
        old.save()
        Blog.objects.create(owner=self.minju, address="minju-new", name="새 한채")
        self.assertEqual(Blog.objects.filter(owner=self.minju).count(), 2)

    def test_torn_down_address_stays_reserved(self):
        old = Blog.objects.create(owner=self.minju, address="minju", name="민주의 한채")
        old.deleted_at = timezone.now()
        old.save()
        other = User.objects.create_user("seohyun@example.com", "password123", nickname="서현")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Blog.objects.create(owner=other, address="minju", name="남의 옛 주소")

    def test_active_owner_is_computed_by_db(self):
        blog = Blog.objects.create(owner=self.minju, address="minju", name="민주의 한채")
        blog.refresh_from_db()
        self.assertEqual(blog.active_owner, self.minju.pk)
        blog.deleted_at = timezone.now()
        blog.save()
        blog.refresh_from_db()
        self.assertIsNone(blog.active_owner)


from datetime import timedelta  # noqa: E402

from rest_framework.test import APITestCase  # noqa: E402

from apps.accounts.tests import make_member  # noqa: E402
from apps.community.models import Subscription  # noqa: E402
from apps.moderation.models import UserSanction  # noqa: E402
from apps.posts.models import Post  # noqa: E402


class BlogApiTests(APITestCase):
    def setUp(self):
        self.minju = make_member()
        self.seohyun = make_member("seohyun@example.com", "서현")

    def build(self, user, address="minju", name="민주의 한채"):
        self.client.force_authenticate(user)
        return self.client.post("/api/blogs", {"address": address, "name": name}, format="json")

    def test_address_available_reasons(self):
        self.build(self.seohyun, "seohyun", "서현의 한채")
        self.client.force_authenticate(self.minju)
        check = lambda a: self.client.get("/api/blogs/address-available", {"address": a}).json()["reason"]
        self.assertEqual(check("seohyun"), "TAKEN")
        self.assertEqual(check("admin"), "RESERVED")
        self.assertEqual(check("Minju"), "INVALID")
        self.assertEqual(check("-minju"), "INVALID")
        self.assertEqual(check("abc"), "INVALID")
        self.assertIsNone(check("minju"))

    def test_visitors_cannot_build(self):
        res = self.client.post("/api/blogs", {"address": "minju", "name": "민주의 한채"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_build_once(self):
        res = self.build(self.minju)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["address"], "minju")
        self.assertTrue(res.json()["is_owner"])
        res = self.build(self.minju, "minju-two", "두 번째")
        self.assertEqual(res.status_code, 409)
        self.assertEqual(self.client.get("/api/auth/me").json()["user"]["blog_address"], "minju")

    def test_detail_for_visitor(self):
        self.build(self.minju)
        self.client.force_authenticate(None)
        res = self.client.get("/api/blogs/minju")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["owner"]["nickname"], "민주")
        self.assertFalse(body["is_owner"])
        self.assertEqual(body["subscriber_count"], 0)

    def test_unknown_or_torn_down_blog_is_404(self):
        self.assertEqual(self.client.get("/api/blogs/nobody").status_code, 404)
        self.build(self.minju)
        Blog.objects.filter(address="minju").update(deleted_at=timezone.now())
        self.assertEqual(self.client.get("/api/blogs/minju").status_code, 404)

    def test_suspended_owner_blog_is_hidden_from_others(self):
        self.build(self.minju)
        UserSanction.objects.create(user=self.minju, admin=self.seohyun, reason="제한", starts_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.client.get("/api/blogs/minju").status_code, 200)  # 주인 본인
        self.client.force_authenticate(self.seohyun)
        self.assertEqual(self.client.get("/api/blogs/minju").status_code, 404)

    def test_only_owner_can_update(self):
        self.build(self.minju)
        self.client.force_authenticate(self.seohyun)
        self.assertEqual(self.client.patch("/api/blogs/minju", {"name": "뺏기"}, format="json").status_code, 403)
        self.client.force_authenticate(self.minju)
        res = self.client.patch("/api/blogs/minju", {"name": "새 현판", "description": "소개"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "새 현판")

    def test_post_count_follows_visibility(self):
        self.build(self.minju)
        blog = Blog.objects.get(address="minju")
        common = {"blog": blog, "content": "x", "content_text": "x", "status": "PUBLISHED", "published_at": timezone.now()}
        Post.objects.create(post_no=1, visibility="PUBLIC", **common)
        Post.objects.create(post_no=2, visibility="SUBSCRIBERS", **common)
        Post.objects.create(post_no=3, visibility="PRIVATE", **common)
        Post.objects.create(blog=blog, content="x", content_text="x")  # 임시저장

        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/blogs/minju").json()["post_count"], 1)
        self.client.force_authenticate(self.seohyun)
        self.assertEqual(self.client.get("/api/blogs/minju").json()["post_count"], 1)
        Subscription.objects.create(blog=blog, subscriber=self.seohyun)
        body = self.client.get("/api/blogs/minju").json()
        self.assertEqual((body["post_count"], body["subscriber_count"], body["is_subscribed"]), (2, 1, True))
        self.client.force_authenticate(self.minju)
        self.assertEqual(self.client.get("/api/blogs/minju").json()["post_count"], 3)
