from django.contrib.auth.tokens import default_token_generator
from django.core.mail import BadHeaderError
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User
from .serializers import (
    LoginSerializer, LogoutSerializer, PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer, RegisterSerializer, UserSerializer,
)
from .services import send_password_reset_email, send_verification_email


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        email = request.data.get("email", "")
        user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_email_verified:
            try:
                send_verification_email(user)
            except BadHeaderError:
                pass
        return response


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from students.services import create_student_profile
        if request.user.role == User.ROLE_STUDENT:
            create_student_profile(request.user)
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        user = request.user
        user_fields = {k: request.data[k] for k in ("first_name", "last_name", "phone") if k in request.data}
        for key, value in user_fields.items():
            setattr(user, key, value)
        user.save(update_fields=list(user_fields.keys()) + ["updated_at"] if user_fields else ["updated_at"])

        if user.role == User.ROLE_STUDENT:
            from students.services import create_student_profile
            profile = create_student_profile(user)
            profile_fields = [
                "college", "department", "year", "semester", "date_of_birth",
                "github_url", "linkedin_url", "bio", "profile_image", "resume",
            ]
            changed = []
            for key in profile_fields:
                if key in request.data:
                    setattr(profile, key, request.data[key])
                    changed.append(key)
            if changed:
                profile.save(update_fields=changed + ["updated_at"])
        return Response(UserSerializer(user, context={"request": request}).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if user and user.is_active:
            try:
                send_password_reset_email(user)
            except BadHeaderError:
                return Response({"detail": "Unable to send reset email."}, status=500)
        return Response({"detail": "If an account exists for that email, reset instructions have been sent."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = get_object_or_404(User, pk=user_id)
        except (TypeError, ValueError, OverflowError):
            return Response({"detail": "Invalid reset link."}, status=400)
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response({"detail": "Reset link is invalid or expired."}, status=400)
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "Password reset successfully."})


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        uid = request.query_params.get("uid", "")
        token = request.query_params.get("token", "")
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = get_object_or_404(User, pk=user_id)
        except (TypeError, ValueError, OverflowError):
            return Response({"detail": "Invalid verification link."}, status=400)
        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Verification link is invalid or expired."}, status=400)
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified", "updated_at"])
        return Response({"detail": "Email verified successfully."})


class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_email_verified:
            return Response({"detail": "Email is already verified."})
        send_verification_email(request.user)
        return Response({"detail": "Verification email sent."})


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.ROLE_ADMIN:
            return Response({"detail": "Admin access required."}, status=403)
        qs = User.objects.all().order_by("-date_joined")
        from core.api import paginated_response
        return paginated_response(request, qs, UserSerializer)

    def patch(self, request, pk):
        if request.user.role != User.ROLE_ADMIN:
            return Response({"detail": "Admin access required."}, status=403)
        user = get_object_or_404(User, pk=pk)
        if "role" in request.data:
            if request.data["role"] not in dict(User.ROLE_CHOICES):
                return Response({"detail": "Invalid role."}, status=400)
            user.role = request.data["role"]
        if "is_active" in request.data:
            user.is_active = bool(request.data["is_active"])
        user.save(update_fields=["role", "is_active", "updated_at"])
        return Response(UserSerializer(user).data)
