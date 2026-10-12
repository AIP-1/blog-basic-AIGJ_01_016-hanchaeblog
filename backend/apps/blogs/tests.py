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
