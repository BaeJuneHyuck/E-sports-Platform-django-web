from django.urls import path

from . import views
from django.contrib.auth.decorators import login_required

app_name = 'practice'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('recommend/', views.IndexView.as_view(), name='recommend'),
    path('search/', views.IndexView.as_view(), name='search'),
    path('detail/<int:practice_pk>/', login_required(views.DetailView.comment), name='detail'),
    path('detail/<int:practice_pk>/new_comment', views.DetailView.as_view(), name='new_comment'),
    path('detail/<int:practice_pk>/delete_comment/<int:comment_pk>', views.DetailView.delete, name='delete_comment'),
    path('<int:pk>/attend/', views.AttendView.as_view(), name='attend'),
    path('create/', views.CreateView.post_new, name='create'),
    path('search/create/', views.CreateView.post_new, name='create'),
]
