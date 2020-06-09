from django.urls import path

from .views import UserRegistrationView, UserLoginView, UserVerificationView, ResendVerifyEmailView, UserMypageView, UserlolpageView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required

app_name = 'user'
urlpatterns = [
    path('registration/', UserRegistrationView.as_view(), name='registration'),
    path('login/',  UserLoginView.as_view(), name='login'),
    path('logout/',  LogoutView.as_view(), name='logout'),
    path('mypage/',  login_required(UserMypageView.as_view()), name='mypage'),
    path('mypage/lol',  login_required(UserlolpageView.as_view()), name='lolpage'),
    path('<pk>/verify/<token>/', UserVerificationView.as_view()),
    path('resend_verify_email/', ResendVerifyEmailView.as_view()),
]
