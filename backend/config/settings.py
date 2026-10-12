"""
한채 Django 설정.

비밀 값과 환경마다 다른 값은 backend/.env 에서 읽는다(.env 는 git 에 올리지 않는다).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.environ.get(name, default)


SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG", "0") == "1"

# 서비스 도메인은 아직 미정이다. 정해지면 .env 의 HANCHAE_DOMAIN 에 넣는다(예: hanchae.kr).
HANCHAE_DOMAIN = env("HANCHAE_DOMAIN", "")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".localhost"]
if HANCHAE_DOMAIN:
    ALLOWED_HOSTS += [HANCHAE_DOMAIN, f".{HANCHAE_DOMAIN}"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 외부 패키지
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.kakao",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.naver",
    # 한채
    "apps.accounts",
    "apps.blogs",
    "apps.posts",
    "apps.community",
    "apps.rankings",
    "apps.moderation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# 데이터베이스: MySQL 8.4, utf8mb4 / utf8mb4_0900_as_ci (ERD REQ-001)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", "hanchae"),
        "USER": env("DB_USER", "hanchae"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "127.0.0.1"),
        "PORT": env("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            "NAME": "test_hanchae",
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_0900_as_ci",
        },
    }
}


# 회원
AUTH_USER_MODEL = "accounts.User"

# 비밀번호는 Argon2 로 해시한다 (ERD REQ-002)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# django-allauth: 아이디 없이 이메일로 로그인, 이메일 인증 필수 (AUTH-01)
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# allauth 의 EmailAddress 는 조건부 유일 제약을 쓰는데 MySQL 은 이를 지원하지 않는다.
# 같은 이메일 중복은 users.email 유일 제약과 ACCOUNT_UNIQUE_EMAIL 이 대신 막는다.
SILENCED_SYSTEM_CHECKS = ["models.W036"]

# 개발 중에는 인증 메일을 터미널에 찍는다
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# 로그인 유지: 마지막 사용 기준 2주 (기능명세서 9.2)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
if HANCHAE_DOMAIN:
    # 모든 한채 서브도메인에서 로그인이 이어지게 한다 (API 명세서 2.2)
    SESSION_COOKIE_DOMAIN = f".{HANCHAE_DOMAIN}"
    CSRF_COOKIE_DOMAIN = f".{HANCHAE_DOMAIN}"
    CSRF_TRUSTED_ORIGINS = [f"https://{HANCHAE_DOMAIN}", f"https://*.{HANCHAE_DOMAIN}"]
    CORS_ALLOWED_ORIGIN_REGEXES = [rf"^https://([a-z0-9-]+\.)?{HANCHAE_DOMAIN.replace('.', r'\.')}$"]
else:
    CSRF_TRUSTED_ORIGINS = ["http://localhost:5500", "http://127.0.0.1:5500"]
    CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://([a-z0-9-]+\.)?localhost(:\d+)?$", r"^http://127\.0\.0\.1(:\d+)?$"]
CORS_ALLOW_CREDENTIALS = True


# Django REST Framework (API 명세서 2장)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "apps.common.errors.exception_handler",
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}


# 언어 · 시각: UTC 로 저장하고 화면에서 한국 시간으로 보여 준다 (ERD REQ-001)
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# 이미지 업로드 상한 10MB (ERD REQ-004)
MAX_IMAGE_BYTES = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
