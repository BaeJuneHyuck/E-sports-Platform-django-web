from django.urls import path

from . import views

app_name = 'practice'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/attend/', views.AttendView.as_view(), name='attend'),
]