from rest_framework import serializers
from .models import Skill, StudentProfile, StudentSkill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "category", "description", "target_score"]


class StudentSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        source="skill", queryset=Skill.objects.all(), write_only=True
    )

    class Meta:
        model = StudentSkill
        fields = ["id", "skill", "skill_id", "current_score", "target_score", "practice_count", "last_updated"]
        read_only_fields = ["last_updated"]

    def validate_current_score(self, value):
        if value > 100:
            raise serializers.ValidationError("Current score must be between 0 and 100.")
        return value

    def validate_target_score(self, value):
        if value > 100:
            raise serializers.ValidationError("Target score must be between 0 and 100.")
        return value


class StudentProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    skills = StudentSkillSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "name", "email", "register_number", "college", "department", "year", "semester",
            "date_of_birth", "profile_image", "github_url", "linkedin_url", "resume", "bio", "skills",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "name", "email", "register_number", "created_at", "updated_at", "skills"]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
