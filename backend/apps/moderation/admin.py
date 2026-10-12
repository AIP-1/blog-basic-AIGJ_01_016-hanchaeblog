from django.contrib import admin

from .models import AdminLog, UserSanction

admin.site.register(UserSanction)
admin.site.register(AdminLog)
