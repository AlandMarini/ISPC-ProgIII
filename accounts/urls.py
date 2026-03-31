from django.urls import path
from .views import OtpView, RegisterView, LoginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('otpview/', OtpView.as_view(), name='otpview')
]