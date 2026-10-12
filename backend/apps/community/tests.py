from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.blogs.models import Blog
from apps.posts.models import Post

from .models import PostLike, Subscription


class CommunityRuleTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("minju@example.com", "password123", nickname="민주")
        self.reader = User.objects.create_user("seohyun@example.com", "password123", nickname="서현")
        self.blog = Blog.objects.create(owner=self.owner, address="minju", name="민주의 한채")
        self.post = Post.objects.create(
            blog=self.blog,
            post_no=1,
            title="첫 기록",
            content="<p>본문</p>",
            content_text="본문",
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )

    def test_like_once_per_post(self):
        """공감은 회원마다 글 하나에 한 번 (ERD REQ-010)."""
        PostLike.objects.create(post=self.post, user=self.reader)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PostLike.objects.create(post=self.post, user=self.reader)

    def test_subscribe_once_per_blog(self):
        """이웃은 한채마다 한 번 (ERD REQ-011)."""
        Subscription.objects.create(blog=self.blog, subscriber=self.reader)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subscription.objects.create(blog=self.blog, subscriber=self.reader)
