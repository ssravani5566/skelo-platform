from rest_framework import serializers

from .models import Assignment, AssignmentSubmission, AssignmentEvaluation


class AssignmentSerializer(serializers.ModelSerializer):
    submission = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "description",
            "instructions",
            "duration_minutes",
            "due_date",
            "max_marks",
            "status",
            "attachment",
            "created_by",
            "created_at",
            "submission",
        ]
        read_only_fields = [
            "created_by",
            "created_at",
            "submission",
        ]

    def validate_duration_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Duration must be greater than 0 minutes."
            )
        return value

    def validate_max_marks(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Maximum marks must be greater than 0."
            )
        return value

    def get_submission(self, obj):
        student = self.context.get("student")
        if not student:
            return None

        sub = (
            obj.submissions
            .filter(student=student)
            .select_related("evaluation")
            .first()
        )

        if not sub:
            return None

        return AssignmentSubmissionSerializer(sub).data


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    feedback = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id",
            "assignment",
            "answer_text",
            "submitted_file",
            "status",
            "submitted_at",
            "score",
            "feedback",
        ]
        read_only_fields = [
            "id",
            "assignment",
            "status",
            "submitted_at",
            "score",
            "feedback",
        ]

    def get_score(self, obj):
        return (
            float(obj.evaluation.marks)
            if hasattr(obj, "evaluation")
            else None
        )

    def get_feedback(self, obj):
        return (
            obj.evaluation.feedback
            if hasattr(obj, "evaluation")
            else ""
        )


class AssignmentEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentEvaluation
        fields = ["marks", "feedback"]
