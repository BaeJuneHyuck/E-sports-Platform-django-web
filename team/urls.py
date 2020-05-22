from django.urls import path

from .views import IndexView, CreateView, DetailView, InviteView,AttendView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required


app_name = 'team'
urlpatterns = [
    path('',  login_required(IndexView.as_view()), name='index'),
    path('detail/<int:pk>/', DetailView.as_view(), name='detail'),
    path('invite/<int:pk>/', login_required(InviteView.as_view()), name='invite'),
    path('create/', login_required(CreateView.post_new), name='teamCreate'),
    path('list/',  login_required(IndexView.as_view()), name='teamList'),

    path('attend/<int:pk>/', login_required(AttendView.post_new), name='attend'),

]
