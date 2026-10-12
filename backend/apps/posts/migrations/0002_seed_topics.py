"""골목 10개를 넣는다 (ERD REQ-007, 기능명세서 9.2). 골목은 이 마이그레이션으로만 넣고 바꾼다."""

from django.db import migrations

TOPICS = [
    ("일상", "daily"),
    ("여행·맛집", "travel"),
    ("IT·개발", "it"),
    ("문화·연예", "culture"),
    ("책·영화", "books"),
    ("반려동물", "pets"),
    ("요리", "cooking"),
    ("스포츠", "sports"),
    ("경제·재테크", "finance"),
    ("기타", "etc"),
]


def add_topics(apps, schema_editor):
    Topic = apps.get_model("posts", "Topic")
    for order, (name, slug) in enumerate(TOPICS, start=1):
        Topic.objects.update_or_create(slug=slug, defaults={"name": name, "sort_order": order})


def remove_topics(apps, schema_editor):
    Topic = apps.get_model("posts", "Topic")
    Topic.objects.filter(slug__in=[slug for _, slug in TOPICS]).delete()


class Migration(migrations.Migration):
    dependencies = [("posts", "0001_initial")]

    operations = [migrations.RunPython(add_topics, remove_topics)]
