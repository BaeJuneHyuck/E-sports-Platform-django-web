from django.urls import path

from .views import IndexView, CreateView, DetailView, InviteView, AttendView, ListView,MyteamView,InvitationView, MyInvitationView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required


app_name = 'team'
urlpatterns = [
    path('',  login_required(IndexView.as_view()), name='index'),
    path('detail/<int:pk>/', DetailView.as_view(), name='detail'),
    path('invite/<int:pk>/', login_required(InviteView.as_view()), name='invite'),
    path('create/', login_required(CreateView.post_new), name='teamCreate'),
    path('list/',  login_required(ListView.as_view()), name='list'),

    path('myteam/',  login_required(MyteamView.as_view()), name='myteam'),
    path('myinvitation/',  login_required(MyInvitationView.as_view()), name='myinvitation'),
    path('attend/<int:pk>/', login_required(AttendView.post_new), name='attend'),
    path('invitation/<int:pk>/', login_required(InvitationView.as_view()), name='invitation'),
]
