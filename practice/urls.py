from django.urls import path

from . import views
from django.contrib.auth.decorators import login_required

app_name = 'practice'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('detail/<int:pk>/', views.DetailView.comment, name='detail'),
    path('detail/<int:pk>/new_comment', views.DetailView.as_view(), name='new_comment'),
    path('<int:pk>/attend/', views.AttendView.as_view(), name='attend'),
    path('create/', login_required(views.CreateView.post_new), name='create'),
]
