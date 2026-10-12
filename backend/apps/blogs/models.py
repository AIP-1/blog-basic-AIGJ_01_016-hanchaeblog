from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models

ADDRESS_VALIDATOR = RegexValidator(
    r"^[a-z0-9](?:[a-z0-9-]{2,30})[a-z0-9]$",
    "한채 주소는 영문 소문자 · 숫자 · 하이픈 4~32자이고, 하이픈으로 시작하거나 끝날 수 없어요.",
)


class Blog(models.Model):
    """한채 (ERD blogs, REQ-003).

    살아 있는 한채는 회원당 하나다. 삭제되지 않은 한채만 active_owner 에 주인 ID 가 들어가고,
    그 열에 유일 제약을 걸어 DB 가 직접 막는다. 허문 한채의 주소는 행이 남아 있으므로 영구히 예약된다.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="blogs", verbose_name="주인"
    )
    address = models.CharField("한채 주소", max_length=32, unique=True, validators=[ADDRESS_VALIDATOR])
    name = models.CharField("한채 이름", max_length=40, validators=[MinLengthValidator(1)])
    description = models.CharField("주인 소개", max_length=200, blank=True, default="")
    profile_image = models.ImageField("프로필 이미지", max_length=255, upload_to="blogs/", null=True, blank=True)
    last_post_no = models.PositiveIntegerField("마지막으로 쓴 글 번호", default=0)
    deleted_at = models.DateTimeField("허문 시각", null=True, blank=True)
    active_owner = models.GeneratedField(
        expression=models.Case(
            models.When(deleted_at__isnull=True, then=models.F("owner_id")),
            default=models.Value(None),
        ),
        output_field=models.BigIntegerField(null=True),
        db_persist=True,
        db_column="active_owner_id",
        verbose_name="살아 있는 한채의 주인",
    )
    created_at = models.DateTimeField("생성 일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정 일시", auto_now=True)

    class Meta:
        db_table = "blogs"
        verbose_name = "한채"
        verbose_name_plural = "한채"
        constraints = [
            models.UniqueConstraint(fields=["active_owner"], name="uk_blogs_active_owner"),
        ]

    def __str__(self):
        return f"{self.name} ({self.address})"

    @property
    def is_alive(self):
        return self.deleted_at is None
