from django.urls import path

from . import views
from django.contrib.auth.decorators import login_required

app_name = 'practice'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('list/', views.TotalListView.as_view(), name='list'),
    path('recommend/', views.IndexView.as_view(), name='recommend'),
    path('list/search/', views.TotalListView.as_view(), name='search'),
    path('list/sort/title', views.SortTitleListView.as_view(), name='sort_title'),
    path('list/sort/tier', views.SortTierListView.as_view(), name='sort_tier'),
    path('list/sort/game', views.SortGameListView.as_view(), name='sort_game'),
    path('list/sort/practice_time', views.SortPracticeTimeListView.as_view(), name='sort_practice_time'),
    path('list/detail/<int:pk>/', login_required(views.DetailView.as_view()), name='detail'),
    path('list/detail/<int:practice_pk>/new_comment', login_required(views.DetailView.new_comment), name='new_comment'),
    path('list/detail/<int:practice_pk>/delete_comment/<int:comment_pk>', views.DetailView.delete, name='delete_comment'),
    path('list/detail/<int:practice_pk>/delete_all_comment', views.DetailView.delete_all, name='delete_all_comment'),
    path('myprac/', login_required(views.MyListView.as_view()), name='myprac'),
    path('list/create/', views.CreateView.post_new, name='create'),
    path('list/search/create/', views.CreateView.post_new, name='create'),
]
