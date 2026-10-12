from django.contrib import admin

from .models import Comment, GuestbookEntry, PostLike, Subscription

admin.site.register(Comment)
admin.site.register(GuestbookEntry)
admin.site.register(PostLike)
admin.site.register(Subscription)
