from rest_framework import serializers
from .models import Assessment, AssessmentQuestion, Question, StudentAssessment, StudentAnswer

class StudentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "option_a", "option_b", "option_c", "option_d", "marks", "difficulty", "coding_language", "starter_code", "input_format", "output_format", "constraints"]

class AssessmentListSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    assigned_student_count = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    attempt_id = serializers.SerializerMethodField()
    class Meta:
        model = Assessment
        fields = ["id", "title", "description", "assessment_type", "duration_minutes", "total_marks", "passing_marks", "is_published", "start_at", "end_at", "created_at", "questions", "status", "attempt_id", "assigned_student_count"]
    def get_questions(self,obj): return obj.assessment_questions.count()
    def get_assigned_student_count(self,obj): return obj.assigned_students.count()
    def get_status(self, obj):
        from django.utils import timezone
        now = timezone.now()
        student = self.context.get("student")
        attempt = StudentAssessment.objects.filter(student=student, assessment=obj).first() if student else None
        if attempt and attempt.status == "EVALUATED": return "Completed"
        if not obj.is_published: return "Upcoming"
        if obj.start_at and now < obj.start_at: return "Upcoming"
        if obj.end_at and now > obj.end_at: return "Closed"
        return "Open"
    def get_attempt_id(self, obj):
        student = self.context.get("student")
        attempt = StudentAssessment.objects.filter(student=student, assessment=obj).first() if student else None
        return attempt.id if attempt else None

class AssessmentDetailSerializer(AssessmentListSerializer):
    questions_data = serializers.SerializerMethodField()
    class Meta(AssessmentListSerializer.Meta):
        fields = AssessmentListSerializer.Meta.fields + ["questions_data"]
    def get_questions_data(self, obj):
        return [StudentQuestionSerializer(aq.question).data for aq in obj.assessment_questions.select_related("question").order_by("order")]

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = ["id", "question", "answer_text", "is_correct", "marks_awarded", "answered_at"]
        read_only_fields = ["id", "is_correct", "marks_awarded", "answered_at"]

class AttemptSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    assessment_type = serializers.CharField(source="assessment.assessment_type", read_only=True)
    total_questions = serializers.SerializerMethodField()
    answered = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()
    wrong_answers = serializers.SerializerMethodField()
    unanswered = serializers.SerializerMethodField()
    total_marks = serializers.SerializerMethodField()
    passed = serializers.SerializerMethodField()
    answers = StudentAnswerSerializer(many=True, read_only=True)
    class Meta:
        model = StudentAssessment
        fields = ["id", "assessment", "assessment_title", "assessment_type", "status", "score", "percentage", "total_marks", "total_questions", "answered", "correct_answers", "wrong_answers", "unanswered", "passed", "started_at", "submitted_at", "evaluated_at", "answers"]

    def _answers(self,obj):
        return list(obj.answers.all())
    def get_total_questions(self,obj):
        return obj.assessment.assessment_questions.count()
    def get_answered(self,obj):
        return obj.answers.count()
    def get_correct_answers(self,obj):
        return obj.answers.filter(is_correct=True).count()
    def get_wrong_answers(self,obj):
        return obj.answers.filter(is_correct=False).count()
    def get_unanswered(self,obj):
        return max(self.get_total_questions(obj)-self.get_answered(obj),0)
    def get_total_marks(self,obj):
        return sum((aq.marks if aq.marks is not None else aq.question.marks) for aq in obj.assessment.assessment_questions.select_related("question"))
    def get_passed(self,obj):
        passing=float(obj.assessment.passing_marks or 0)
        return float(obj.score) >= passing if passing else float(obj.percentage) >= 40
