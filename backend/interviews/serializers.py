from rest_framework import serializers
from .models import Interview, InterviewQuestion, InterviewAnswer, InterviewFeedback
class InterviewFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model=InterviewFeedback
        fields=["id","strengths","improvement_areas","technical_score","communication_score","confidence_score","overall_feedback","created_at"]
class InterviewAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model=InterviewAnswer
        fields=["id","interview_question","answer_text","audio_url","score","feedback","answered_at"]
        read_only_fields=["id","score","feedback","answered_at"]
class InterviewQuestionSerializer(serializers.ModelSerializer):
    latest_answer=serializers.SerializerMethodField()
    class Meta:
        model=InterviewQuestion
        fields=["id","question_text","category","order","latest_answer"]
    def get_latest_answer(self,obj):
        a=obj.answers.order_by("-answered_at").first(); return InterviewAnswerSerializer(a).data if a else None
class InterviewSerializer(serializers.ModelSerializer):
    status=serializers.CharField(read_only=True)
    feedback=InterviewFeedbackSerializer(read_only=True)
    class Meta:
        model=Interview
        fields=["id","title","interview_type","student","interviewer","scheduled_at","status","role","overall_score","created_at","feedback"]
        read_only_fields=["created_at","overall_score"]
