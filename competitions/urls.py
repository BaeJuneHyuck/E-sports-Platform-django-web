from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = 'competitions'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('attend/<int:pk>/', views.AttendView.as_view(), name='attend'),
    path('ongoing/', views.OngoingView.as_view(), name='ongoing'),
    path('scheduled/', views.ScheduledView.as_view(), name='scheduled'),
    path('past/', views.PastView.as_view(), name='past'),
    path('create/', views.CreateView.post_new, name='create'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
