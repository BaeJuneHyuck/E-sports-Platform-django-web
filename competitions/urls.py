from django.urls import path

from . import views

app_name = 'competitions'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/attend/', views.AttendView.as_view(), name='attend'),
    path('ongoing/', views.OngoingView.as_view(), name='ongoing'),
    path('scheduled/', views.ScheduledView.as_view(), name='scheduled'),
    path('past/', views.PastView.as_view(), name='past'),
]