from django.urls import path

from . import views
from django.contrib.auth.decorators import login_required

app_name = 'practice'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('list/', views.TotalListView.as_view(), name='list'),
    path('recommend/', views.IndexView.as_view(), name='recommend'),
    path('list/search/', views.TotalListView.as_view(), name='search'),
    path('list/detail/<int:practice_pk>/', login_required(views.DetailView.comment), name='detail'),
    path('list/detail/<int:practice_pk>/new_comment', views.DetailView.comment, name='new_comment'),
    path('list/detail/<int:practice_pk>/delete_comment/<int:comment_pk>', views.DetailView.delete, name='delete_comment'),
    path('<int:pk>/attend/', views.AttendView.as_view(), name='attend'),
    path('list/create/', views.CreateView.post_new, name='create'),
    path('list/search/create/', views.CreateView.post_new, name='create'),
]
