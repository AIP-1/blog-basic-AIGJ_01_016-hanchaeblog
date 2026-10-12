from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.blogs.models import Blog

from .models import Category, Post, Tag, Topic


class PostsTestBase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("minju@example.com", "password123", nickname="민주")
        self.blog = Blog.objects.create(owner=self.owner, address="minju", name="민주의 한채")

    def publish(self, blog, post_no, **extra):
        return Post.objects.create(
            blog=blog,
            post_no=post_no,
            title=f"기록 {post_no}",
            content="<p>본문</p>",
            content_text="본문",
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
            **extra,
        )


class TopicSeedTests(TestCase):
    def test_ten_topics_are_seeded(self):
        self.assertEqual(Topic.objects.count(), 10)
        self.assertEqual(Topic.objects.first().slug, "daily")


class CategoryRuleTests(PostsTestBase):
    """같은 단계 안에서 방 이름은 겹칠 수 없다 (ERD REQ-005)."""

    def test_same_name_at_top_level_is_rejected(self):
        Category.objects.create(blog=self.blog, name="개발")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Category.objects.create(blog=self.blog, name="개발")

    def test_same_name_under_different_parents_is_allowed(self):
        travel = Category.objects.create(blog=self.blog, name="여행")
        daily = Category.objects.create(blog=self.blog, name="일상")
        Category.objects.create(blog=self.blog, parent=travel, name="사진")
        Category.objects.create(blog=self.blog, parent=daily, name="사진")
        self.assertEqual(Category.objects.filter(name="사진").count(), 2)


class TagRuleTests(PostsTestBase):
    def test_tag_names_ignore_case(self):
        """영문 대소문자만 다르면 같은 태그 (ERD REQ-006, DB 정렬 규칙 utf8mb4_0900_as_ci)."""
        Tag.objects.create(blog=self.blog, name="Django")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Tag.objects.create(blog=self.blog, name="django")


class PostRuleTests(PostsTestBase):
    def test_post_no_is_unique_within_a_blog(self):
        self.publish(self.blog, 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.publish(self.blog, 1)

    def test_same_post_no_in_another_blog_is_fine(self):
        other_owner = User.objects.create_user("seohyun@example.com", "password123", nickname="서현")
        other_blog = Blog.objects.create(owner=other_owner, address="seohyun", name="서현의 한채")
        self.publish(self.blog, 1)
        self.publish(other_blog, 1)
        self.assertEqual(Post.objects.filter(post_no=1).count(), 2)

    def test_published_post_needs_number_and_date(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Post.objects.create(
                blog=self.blog, title="번호 없는 발행", content="x", content_text="x", status=Post.Status.PUBLISHED
            )

    def test_subscribers_visibility_is_allowed(self):
        post = self.publish(self.blog, 1, visibility=Post.Visibility.SUBSCRIBERS)
        self.assertEqual(post.visibility, "SUBSCRIBERS")

    def test_unknown_visibility_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.publish(self.blog, 1, visibility="FRIENDS")

    def test_hiding_needs_a_reason(self):
        post = self.publish(self.blog, 1)
        post.hidden_at = timezone.now()
        with self.assertRaises(IntegrityError), transaction.atomic():
            post.save()

    def test_same_client_token_cannot_publish_twice(self):
        self.publish(self.blog, 1, client_token="6f1c2b9e-0d7a-4c55-9a77-1f2e3d4c5b6a")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.publish(self.blog, 2, client_token="6f1c2b9e-0d7a-4c55-9a77-1f2e3d4c5b6a")
