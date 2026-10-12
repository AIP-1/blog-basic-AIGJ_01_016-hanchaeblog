from django.urls import path

from . import views

urlpatterns = [
    path("blogs/<str:address>/posts/<int:no>/comments", views.PostCommentsView.as_view()),
    path("blogs/<str:address>/posts/<int:no>/like", views.PostLikeView.as_view()),
    path("blogs/<str:address>/subscription", views.SubscriptionView.as_view()),
    path("comments/<int:comment_id>", views.CommentDetailView.as_view()),
    path("me/feed", views.FeedView.as_view()),
]
