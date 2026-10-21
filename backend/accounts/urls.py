from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    AdminUserListView, ForgotPasswordView, LoginView, LogoutView, ProfileView,
    RegisterView, ResendVerificationView, ResetPasswordView, VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
    path("users/", AdminUserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", AdminUserListView.as_view(), name="user-detail"),
]
