from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from students.models import StudentProfile
from .models import User


class StudentProfileInlineSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    resume = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = StudentProfile
        fields = [
            "register_number", "college", "department", "year", "semester", "date_of_birth",
            "profile_image", "github_url", "linkedin_url", "resume", "bio",
        ]
        read_only_fields = ["register_number"]


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    student_profile = StudentProfileInlineSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "name", "role",
            "phone", "is_email_verified", "student_profile", "date_joined", "updated_at",
        ]
        read_only_fields = ["id", "role", "is_email_verified", "date_joined", "updated_at"]

    def get_name(self, obj):
        return obj.get_full_name() or obj.username


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]
        read_only_fields = ["id"]

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data, role=User.ROLE_STUDENT)
        user.set_password(password)
        user.save()
        from students.services import create_student_profile
        create_student_profile(user)
        return user

    def to_representation(self, instance):
        return {"user": UserSerializer(instance, context=self.context).data}


class LoginSerializer(serializers.Serializer):
    # `identifier` is the canonical field. Email/username/admin_id remain
    # accepted for compatibility with older SCOTT frontends.
    identifier = serializers.CharField(required=False, allow_blank=True)
    admin_id = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = (
            attrs.get("identifier")
            or attrs.get("admin_id")
            or attrs.get("email")
            or attrs.get("username")
            or ""
        ).strip()

        if not identifier:
            raise serializers.ValidationError({
                "identifier": "Email address or Admin ID is required."
            })

        password = attrs.get("password", "")
        if password == "":
            raise serializers.ValidationError({
                "password": "Password is required."
            })

        # User.USERNAME_FIELD is email, but Admin is intentionally a
        # username/ID. Resolve either form to the real User first.
        if "@" in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
        else:
            user_obj = User.objects.filter(username__iexact=identifier).first()

        if not user_obj:
            raise serializers.ValidationError({
                "identifier": "No account was found for this email or Admin ID."
            })

        user = authenticate(username=user_obj.email, password=password)
        if not user or not user.is_active:
            raise serializers.ValidationError({
                "password": "Incorrect password."
            })

        refresh = RefreshToken.for_user(user)
        return {
            "user": UserSerializer(user, context=self.context).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value):
        validate_password(value)
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
