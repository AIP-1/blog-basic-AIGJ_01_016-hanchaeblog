"""코드 검토에서 나온 문제들 (사진 주소 · 큰 사진 · 화면 파일 경로 · 열려 있던 allauth 화면)."""

import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image as PILImage
from rest_framework.test import APITestCase

from apps.accounts.tests import make_member

from . import content

TEMP_MEDIA = tempfile.mkdtemp(prefix="hanchae-test-media-")


@override_settings(ALLOWED_HOSTS=["hanchae.java21.net", ".hanchae.java21.net", "localhost"])
class BodyImageTests(SimpleTestCase):
    def src(self, url):
        return content.image_paths(content.sanitize(f'<img src="{url}">')), content.sanitize(f'<img src="{url}">')

    def test_only_our_host_and_stored_as_relative(self):
        for url in ("/media/images/a.png", "http://hanchae.java21.net/media/images/a.png", "https://localhost:8000/media/images/a.png"):
            paths, html = self.src(url)
            self.assertEqual(paths, ["images/a.png"], url)
            self.assertEqual(html, '<img src="/media/images/a.png">', url)

    def test_other_hosts_are_dropped_even_with_media_path(self):
        for url in ("https://evil.com/media/x.gif", "//evil.com/media/x.gif", "https://evil.hanchae.java21.net.evil.com/media/x.gif"):
            self.assertEqual(self.src(url), ([], ""), url)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UploadLimitTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client.force_authenticate(make_member())

    def upload(self, img, fmt="PNG"):
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        return self.client.post("/api/images", {"file": SimpleUploadedFile("a.png", buffer.getvalue(), "image/png")}, format="multipart")

    def test_urls_are_relative(self):
        body = self.upload(PILImage.new("RGB", (100, 80))).json()
        self.assertTrue(body["url"].startswith("/media/images/"))
        self.assertTrue(body["thumb_url"].startswith("/media/images/thumbs/"))

    def test_too_many_pixels_is_413_not_500(self):
        res = self.upload(PILImage.new("1", (9000, 5000)))  # 4,500만 화소, 흑백이라 파일은 작다
        self.assertEqual(res.status_code, 413)

    def test_unusual_png_modes_make_thumbnails(self):
        for mode in ("I;16", "1", "LA", "P"):
            self.assertEqual(self.upload(PILImage.new(mode, (60, 40))).status_code, 201, mode)


class FrontendPathTests(TestCase):
    def test_cannot_leave_frontend_folders(self):
        for url in ("/css/../backend/.env", "/js/..%2Fbackend/.env", "/css/%2e%2e/backend/.env", "/css\\..\\backend\\.env"):
            self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_pages_and_trailing_slash(self):
        self.assertEqual(self.client.get("/login").status_code, 200)
        res = self.client.get("/login/?next=/write")
        self.assertEqual((res.status_code, res["Location"]), (301, "/login?next=/write"))
        # 서버가 받은 경로가 //evil.com/ 이어도 같은 사이트 안의 /evil.com 으로만 보낸다
        from django.test import RequestFactory

        from config.frontend import frontend

        res = frontend(RequestFactory().get("/"), path="/evil.com/")
        self.assertEqual(res["Location"], "/evil.com")


class AllauthPagesClosedTests(TestCase):
    def test_allauth_pages_are_closed_until_social_login(self):
        for url in ("/accounts/login/", "/accounts/signup/", "/accounts/kakao/login/"):
            self.assertEqual(self.client.get(url).status_code, 404, url)
