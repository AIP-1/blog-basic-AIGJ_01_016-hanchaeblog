from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.blogs.models import Blog

from .models import Category, Image, Post, Tag, Topic


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


import io  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import override_settings  # noqa: E402
from PIL import Image as PILImage  # noqa: E402
from rest_framework.test import APITestCase  # noqa: E402

from apps.accounts.tests import make_member  # noqa: E402

TEMP_MEDIA = tempfile.mkdtemp(prefix="hanchae-test-media-")


def png_bytes(width=1200, height=800):
    buffer = io.BytesIO()
    PILImage.new("RGB", (width, height), (59, 69, 82)).save(buffer, format="PNG")
    return buffer.getvalue()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ImageUploadTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = make_member()
        self.client.force_authenticate(self.user)

    def upload(self, data, name="photo.png", content_type="image/png"):
        return self.client.post("/api/images", {"file": SimpleUploadedFile(name, data, content_type)}, format="multipart")

    def test_upload_makes_thumbnail(self):
        res = self.upload(png_bytes())
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual((body["width"], body["height"]), (1200, 800))
        self.assertTrue(body["thumb_url"].endswith(".webp"))
        image = Image.objects.get(pk=body["id"])
        with PILImage.open(image.thumb_file.path) as thumb:
            self.assertEqual(thumb.width, 480)

    def test_fake_image_is_rejected(self):
        res = self.upload(b"this is not an image", name="evil.png")
        self.assertEqual(res.status_code, 415)
        self.assertEqual(res.json()["error"]["code"], "UNSUPPORTED_FILE")

    @override_settings(MAX_IMAGE_BYTES=100)
    def test_too_large(self):
        res = self.upload(png_bytes())
        self.assertEqual(res.status_code, 413)

    def test_profile_image_from_upload(self):
        image_id = self.upload(png_bytes(64, 64)).json()["id"]
        res = self.client.patch("/api/me", {"profile_image_id": image_id}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIsNotNone(res.json()["user"]["profile_image_url"])
        other = make_member("seohyun@example.com", "서현")
        self.client.force_authenticate(other)
        res = self.client.patch("/api/me", {"profile_image_id": image_id}, format="json")
        self.assertEqual(res.status_code, 400)  # 남이 올린 이미지는 쓸 수 없다

    def test_topics(self):
        res = self.client.get("/api/topics")
        self.assertEqual(len(res.json()), 10)
        self.assertEqual(res.json()[2], {"slug": "it", "name": "IT·개발"})
