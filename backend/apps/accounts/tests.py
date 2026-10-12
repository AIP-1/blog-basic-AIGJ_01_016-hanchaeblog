import re
from datetime import timedelta

from allauth.account.models import EmailAddress
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.moderation.models import UserSanction

from .models import User

SIGNUP = {
    "email": "minju@example.com",
    "password": "hanchae-1234",
    "nickname": "민주",
    "agree_terms": True,
    "agree_privacy": True,
    "over_14": True,
}


def make_member(email="minju@example.com", nickname="민주", password="hanchae-1234", verified=True):
    user = User.objects.create_user(email, password, nickname=nickname)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=verified)
    return user


class SignupFlowTests(APITestCase):
    def test_signup_sends_mail_then_verify_then_login(self):
        res = self.client.post("/api/auth/signup", SIGNUP, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json(), {"email_verification_sent": True})
        self.assertEqual(len(mail.outbox), 1)

        login = {"email": SIGNUP["email"], "password": SIGNUP["password"]}
        self.assertEqual(self.client.post("/api/auth/login", login, format="json").json()["error"]["code"], "EMAIL_NOT_VERIFIED")

        key = re.search(r"confirm-email/([^/\s]+)/", mail.outbox[0].body).group(1)
        self.assertEqual(self.client.post("/api/auth/email/verify", {"key": key}, format="json").status_code, 200)

        res = self.client.post("/api/auth/login", login, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"]["nickname"], "민주")
        self.assertIsNone(res.json()["user"]["blog_address"])

    def test_duplicate_email_and_nickname_conflict(self):
        make_member()
        res = self.client.post("/api/auth/signup", SIGNUP, format="json")
        self.assertEqual(res.status_code, 409)
        self.assertEqual(set(res.json()["error"]["fields"]), {"email", "nickname"})

    def test_email_is_case_insensitive(self):
        make_member()
        res = self.client.post("/api/auth/signup", {**SIGNUP, "email": "MINJU@example.com", "nickname": "다른이"}, format="json")
        self.assertEqual(res.status_code, 409)

    def test_signup_rules(self):
        bad = {**SIGNUP, "password": "short", "nickname": "a", "agree_terms": False, "over_14": False}
        res = self.client.post("/api/auth/signup", bad, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(set(res.json()["error"]["fields"]), {"password", "nickname", "agree_terms", "over_14"})

    def test_bad_verify_key(self):
        res = self.client.post("/api/auth/email/verify", {"key": "nope"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_signup_requires_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        res = client.post("/api/auth/signup", SIGNUP, format="json")
        self.assertEqual(res.status_code, 403)

        client.get("/api/auth/csrf")
        token = client.cookies["csrftoken"].value
        res = client.post("/api/auth/signup", SIGNUP, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(res.status_code, 201)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = make_member()

    def login(self, password="hanchae-1234"):
        return self.client.post("/api/auth/login", {"email": "minju@example.com", "password": password}, format="json")

    def test_me_is_null_for_visitors(self):
        self.assertEqual(self.client.get("/api/auth/me").json(), {"user": None})

    def test_wrong_password(self):
        res = self.login("wrong-password")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], "LOGIN_FAILED")

    def test_login_me_logout(self):
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").json()["user"]["email"], "minju@example.com")
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me").json(), {"user": None})

    def test_logout_needs_login(self):
        res = self.client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], "AUTH_REQUIRED")

    def test_suspended_member_cannot_login(self):
        admin = make_member("admin@example.com", "관리인")
        UserSanction.objects.create(
            user=self.user, admin=admin, reason="스팸 댓글", starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(days=3),
        )
        res = self.login()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["error"]["code"], "SUSPENDED")
        self.assertEqual(res.json()["error"]["detail"]["reason"], "스팸 댓글")

    def test_expired_sanction_allows_login(self):
        admin = make_member("admin@example.com", "관리인")
        UserSanction.objects.create(
            user=self.user, admin=admin, reason="지난 제한", starts_at=timezone.now() - timedelta(days=5),
            ends_at=timezone.now() - timedelta(days=1),
        )
        self.assertEqual(self.login().status_code, 200)


class NicknameAndMeTests(APITestCase):
    def setUp(self):
        self.user = make_member()
        make_member("seohyun@example.com", "서현")

    def test_nickname_available(self):
        get = lambda n: self.client.get("/api/auth/nickname-available", {"nickname": n}).json()
        self.assertEqual(get("서현"), {"available": False, "reason": "TAKEN"})
        self.assertEqual(get("가"), {"available": False, "reason": "INVALID"})
        self.assertEqual(get("새이름"), {"available": True, "reason": None})

    def test_update_nickname(self):
        self.client.force_authenticate(self.user)
        res = self.client.patch("/api/me", {"nickname": "민주2"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"]["nickname"], "민주2")
        res = self.client.patch("/api/me", {"nickname": "서현"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("nickname", res.json()["error"]["fields"])
