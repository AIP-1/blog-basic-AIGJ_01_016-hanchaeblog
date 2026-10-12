from django.db import models


class RankingSnapshot(models.Model):
    """정각 순위 스냅숏 (ERD ranking_snapshots, REQ-008).

    매 정각에 직전 1시간 조회수로 계산해 저장하고, 다음 정각까지 같은 순위를 보여 준다.
    1시간 조회가 없으면 24시간 기준, 그것도 없으면 EMPTY.
    """

    class Kind(models.TextChoices):
        POST = "POST", "지금 많이 읽는 기록"
        BLOGGER = "BLOGGER", "북적이는 한채"

    class Basis(models.TextChoices):
        ONE_HOUR = "1H", "최근 1시간"
        ONE_DAY = "24H", "최근 24시간"
        EMPTY = "EMPTY", "없음"

    kind = models.CharField("종류", max_length=10, choices=Kind.choices)
    window_end = models.DateTimeField("기준 정각")
    basis = models.CharField("기준", max_length=5, choices=Basis.choices)
    created_at = models.DateTimeField("생성 일시", auto_now_add=True)

    class Meta:
        db_table = "ranking_snapshots"
        verbose_name = "순위 스냅숏"
        verbose_name_plural = "순위 스냅숏"
        constraints = [
            models.UniqueConstraint(fields=["kind", "window_end"], name="uk_ranking_snapshots"),
            models.CheckConstraint(condition=models.Q(kind__in=["POST", "BLOGGER"]), name="ck_ranking_snapshots_kind"),
            models.CheckConstraint(
                condition=models.Q(basis__in=["1H", "24H", "EMPTY"]), name="ck_ranking_snapshots_basis"
            ),
        ]


class RankingEntry(models.Model):
    """순위 항목 (ERD ranking_entries). post 와 blog 중 정확히 하나만 채운다(순위 계산 코드가 지킨다)."""

    snapshot = models.ForeignKey(RankingSnapshot, on_delete=models.CASCADE, related_name="entries")
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    blog = models.ForeignKey("blogs.Blog", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    position = models.SmallIntegerField("순위")
    score = models.IntegerField("구간 조회수")

    class Meta:
        db_table = "ranking_entries"
        ordering = ["position"]
        verbose_name = "순위 항목"
        verbose_name_plural = "순위 항목"
        constraints = [
            models.UniqueConstraint(fields=["snapshot", "position"], name="uk_ranking_entries"),
        ]
