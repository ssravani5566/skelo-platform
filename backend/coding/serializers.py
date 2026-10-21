from django.utils.text import slugify
from rest_framework import serializers

from .external import (
    PLATFORM_CHOICES,
    build_external_tags,
    is_external_problem,
    parse_external_tags,
    platform_label,
    validate_platform_url,
)
from .models import ExternalProblemProgress, Problem, Submission, SubmissionResult


class ProblemListSerializer(serializers.ModelSerializer):
    difficulty_label = serializers.CharField(source="get_difficulty_display", read_only=True)
    solved = serializers.SerializerMethodField()
    is_external = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    platform_label = serializers.SerializerMethodField()
    external_url = serializers.SerializerMethodField()
    external_problem_id = serializers.SerializerMethodField()
    external_number = serializers.SerializerMethodField()
    acceptance_rate = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    platform_metric_label = serializers.SerializerMethodField()
    platform_metric_value = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id", "title", "slug", "description", "difficulty", "difficulty_label",
            "topic", "tags", "points", "solved", "is_external", "platform",
            "platform_label", "external_url", "external_problem_id", "external_number",
            "acceptance_rate", "success_rate", "platform_metric_label", "platform_metric_value",
            "premium", "topics",
        ]

    def get_solved(self, obj):
        student = self.context.get("student")
        if not student:
            return None
        if is_external_problem(obj):
            solved_ids = self.context.get("external_solved_ids")
            if solved_ids is not None:
                return obj.id in solved_ids
            return ExternalProblemProgress.objects.filter(student=student, problem=obj).exists()
        solved_ids = self.context.get("local_solved_ids")
        if solved_ids is not None:
            return obj.id in solved_ids
        return Submission.objects.filter(student=student, problem=obj, status="ACCEPTED").exists()

    def _meta(self, obj):
        return parse_external_tags(obj.tags)

    def get_is_external(self, obj):
        return is_external_problem(obj)

    def get_platform(self, obj):
        return self._meta(obj).get("platform")

    def get_platform_label(self, obj):
        platform = self._meta(obj).get("platform")
        return platform_label(platform) if platform else None

    def get_external_url(self, obj):
        return self._meta(obj).get("url")

    def get_external_problem_id(self, obj):
        return self._meta(obj).get("id")

    def get_external_number(self, obj):
        return self._meta(obj).get("number") or self._meta(obj).get("id")

    def get_acceptance_rate(self, obj):
        value = self._meta(obj).get("acceptance")
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def get_success_rate(self, obj):
        value = self._meta(obj).get("success_rate")
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def get_platform_metric_label(self, obj):
        meta = self._meta(obj)
        platform = meta.get("platform")
        if platform == "LEETCODE" and meta.get("acceptance") not in (None, ""):
            return "Acceptance"
        if platform == "HACKERRANK" and meta.get("success_rate") not in (None, ""):
            return "Success"
        if platform == "CODEFORCES" and meta.get("score") not in (None, ""):
            return "Solved"
        return ""

    def get_platform_metric_value(self, obj):
        meta = self._meta(obj)
        platform = meta.get("platform")
        value = meta.get("acceptance") if platform == "LEETCODE" else meta.get("success_rate") if platform == "HACKERRANK" else meta.get("score") if platform == "CODEFORCES" else None
        return value

    def get_premium(self, obj):
        return bool(self._meta(obj).get("premium"))

    def get_topics(self, obj):
        topics = self._meta(obj).get("topics") or []
        return topics if isinstance(topics, list) else []


class ProblemDetailSerializer(ProblemListSerializer):
    samples = serializers.SerializerMethodField()

    class Meta(ProblemListSerializer.Meta):
        fields = ProblemListSerializer.Meta.fields + [
            "input_format", "output_format", "constraints", "samples",
        ]

    def get_samples(self, obj):
        if is_external_problem(obj):
            return []
        return [
            {"id": tc.id, "input": tc.input_data, "expected_output": tc.expected_output, "order": tc.order}
            for tc in obj.test_cases.filter(is_sample=True)
        ]


class ExternalProblemCreateSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=PLATFORM_CHOICES)
    title = serializers.CharField(max_length=200)
    external_url = serializers.URLField()
    external_problem_id = serializers.CharField(max_length=200, required=False, allow_blank=True)
    external_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(choices=Problem.DIFFICULTY_CHOICES, default="EASY")
    topic = serializers.CharField(max_length=100, required=False, allow_blank=True)
    acceptance_rate = serializers.FloatField(required=False, min_value=0, max_value=100, allow_null=True)
    success_rate = serializers.FloatField(required=False, min_value=0, max_value=100, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)
    is_published = serializers.BooleanField(default=True)

    def validate(self, attrs):
        try:
            validate_platform_url(attrs["platform"], attrs["external_url"])
        except ValueError as exc:
            raise serializers.ValidationError({"external_url": str(exc)})
        return attrs

    def create(self, validated_data):
        platform = validated_data.pop("platform")
        url = validated_data.pop("external_url")
        external_id = validated_data.pop("external_problem_id", "")
        external_number = validated_data.pop("external_number", "")
        acceptance = validated_data.pop("acceptance_rate", None)
        success_rate = validated_data.pop("success_rate", None)
        extra_tags = validated_data.pop("tags", [])
        base_slug = slugify(f"{platform}-{external_id or external_number or validated_data['title']}")[:230] or "external-problem"
        slug = base_slug
        index = 2
        while Problem.objects.filter(slug=slug).exists():
            slug = f"{base_slug[:220]}-{index}"
            index += 1
        tags = build_external_tags(
            platform, url, external_id, extra_tags,
            number=external_number,
            acceptance=acceptance,
            success_rate=success_rate,
        )
        return Problem.objects.create(slug=slug, tags=tags, points=0, **validated_data)


class ExternalProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProblemProgress
        fields = ["id", "problem", "solved_at"]
        read_only_fields = fields


class SubmissionResultSerializer(serializers.ModelSerializer):
    test_case = serializers.IntegerField(source="test_case_id")

    class Meta:
        model = SubmissionResult
        fields = ["test_case", "passed", "actual_output", "runtime_ms", "error_message"]


class SubmissionSerializer(serializers.ModelSerializer):
    results = SubmissionResultSerializer(many=True, read_only=True)
    problem_title = serializers.CharField(source="problem.title", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id", "problem", "problem_title", "language", "source_code", "status",
            "runtime_ms", "memory_kb", "passed_test_cases", "total_test_cases",
            "error_message", "submitted_at", "results",
        ]
        read_only_fields = [
            "id", "status", "runtime_ms", "memory_kb", "passed_test_cases",
            "total_test_cases", "error_message", "submitted_at", "results",
        ]


class SubmissionCreateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=Submission.LANGUAGE_CHOICES)
    source_code = serializers.CharField(max_length=20000)
