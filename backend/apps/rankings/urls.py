from django.urls import path

from . import views

urlpatterns = [
    path("rankings/posts", views.PostRankingView.as_view()),
    path("rankings/blogs", views.BlogRankingView.as_view()),
]
