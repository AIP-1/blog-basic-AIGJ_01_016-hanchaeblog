from django.contrib import admin

from .models import RankingEntry, RankingSnapshot

admin.site.register(RankingSnapshot)
admin.site.register(RankingEntry)
