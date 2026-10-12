from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra):
        now = timezone.now()
        extra.setdefault("terms_agreed_at", now)
        extra.setdefault("privacy_agreed_at", now)
        user = self.model(email=self.normalize_email(email) if email else None, **extra)
        user.set_password(password)  # password 가 None 이면 로그인할 수 없는 값이 들어간다 (소셜 전용)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """회원 (ERD users, REQ-002).

    is_staff · is_superuser 는 Django 운영 화면(/django-admin/) 권한이고,
    서비스 관리자(마을 관리인)는 role = ADMIN 으로 따로 정한다.
    """

    class Role(models.TextChoices):
        MEMBER = "MEMBER", "회원"
        ADMIN = "ADMIN", "서비스 관리자"

    email = models.EmailField("이메일", max_length=254, unique=True, null=True, blank=True)
    nickname = models.CharField(
        "닉네임", max_length=20, unique=True, null=True, blank=True, validators=[MinLengthValidator(2)]
    )
    role = models.CharField("역할", max_length=10, choices=Role.choices, default=Role.MEMBER)
    terms_agreed_at = models.DateTimeField("이용약관 동의 시각")
    privacy_agreed_at = models.DateTimeField("개인정보 수집·이용 동의 시각")
    is_active = models.BooleanField("활성", default=True)
    withdrawn_at = models.DateTimeField("탈퇴 시각", null=True, blank=True)
    is_staff = models.BooleanField("운영자", default=False)
    profile_image = models.ImageField("프로필 이미지", max_length=255, upload_to="profiles/", null=True, blank=True)
    created_at = models.DateTimeField("생성 일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정 일시", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "회원"
        verbose_name_plural = "회원"
        constraints = [
            models.CheckConstraint(condition=models.Q(role__in=["MEMBER", "ADMIN"]), name="ck_users_role"),
        ]

    def __str__(self):
        return self.nickname or self.email or f"회원 {self.pk}"

    @property
    def is_service_admin(self):
        return self.role == self.Role.ADMIN
