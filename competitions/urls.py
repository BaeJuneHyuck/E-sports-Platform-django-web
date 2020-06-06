from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'competitions'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('attend/<int:pk>/', login_required(views.AttendView.post_new), name='attend'),
    path('ongoing/', views.OngoingView.as_view(), name='ongoing'),
    path('ongoing/search', views.OngoingView.as_view(), name='ongoing_search'),
    path('scheduled/', views.ScheduledView.as_view(), name='scheduled'),
    path('scheduled/search', views.ScheduledView.as_view(), name='scheduled_search'),
    path('past/', views.PastView.as_view(), name='past'),
    path('create/', views.CreateView.post_new, name='create'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
