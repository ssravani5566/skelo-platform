from rest_framework import serializers

from students.models import StudentProfile
from .models import Assessment, AssessmentQuestion, Question


class AssessmentAdminSerializer(serializers.ModelSerializer):
    assigned_student_ids = serializers.PrimaryKeyRelatedField(
        source="assigned_students",
        many=True,
        queryset=StudentProfile.objects.select_related("user").filter(
            user__role="STUDENT"
        ),
        required=False,
    )
    assigned_student_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "description",
            "assessment_type",
            "duration_minutes",
            "total_marks",
            "passing_marks",
            "is_published",
            "start_at",
            "end_at",
            "assigned_student_ids",
            "assigned_student_count",
        ]

    def get_assigned_student_count(self, obj):
        return obj.assigned_students.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["assigned_student_ids"] = list(
            instance.assigned_students.values_list("id", flat=True)
        )
        return data

    def validate(self, attrs):
        start = attrs.get(
            "start_at", getattr(self.instance, "start_at", None)
        )
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        total = attrs.get(
            "total_marks", getattr(self.instance, "total_marks", 0)
        )
        passing = attrs.get(
            "passing_marks", getattr(self.instance, "passing_marks", 0)
        )

        if start and end and end <= start:
            raise serializers.ValidationError(
                "end_at must be later than start_at"
            )

        if passing > total:
            raise serializers.ValidationError(
                "passing_marks cannot exceed total_marks"
            )

        return attrs


class QuestionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "question_type",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "explanation",
            "difficulty",
            "marks",
            "coding_language",
            "starter_code",
            "input_format",
            "output_format",
            "constraints",
            "test_cases",
        ]

    def validate(self, attrs):
        qtype = attrs.get(
            "question_type",
            getattr(self.instance, "question_type", "MCQ"),
        )

        if qtype == "MCQ":
            if not attrs.get(
                "option_a", getattr(self.instance, "option_a", "")
            ) or not attrs.get(
                "option_b", getattr(self.instance, "option_b", "")
            ):
                raise serializers.ValidationError(
                    "MCQ requires at least options A and B."
                )

            correct = attrs.get(
                "correct_answer",
                getattr(self.instance, "correct_answer", ""),
            )

            if str(correct).upper() not in {"A", "B", "C", "D"}:
                raise serializers.ValidationError(
                    "MCQ correct answer must be A, B, C or D."
                )

        if qtype == "CODING":
            cases = attrs.get(
                "test_cases",
                getattr(self.instance, "test_cases", []),
            ) or []

            if not isinstance(cases, list) or not cases:
                raise serializers.ValidationError(
                    "Coding question requires at least one test case."
                )

            for case in cases:
                if (
                    not isinstance(case, dict)
                    or "input" not in case
                    or "output" not in case
                ):
                    raise serializers.ValidationError(
                        "Each coding test case must contain input and output."
                    )

        return attrs


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    question = QuestionAdminSerializer(read_only=True)

    class Meta:
        model = AssessmentQuestion
        fields = ["id", "question", "order", "marks"]
