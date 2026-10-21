from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Skill, StudentSkill
from .serializers import SkillSerializer, StudentProfileSerializer, StudentSkillSerializer
from .services import get_student_profile


class HealthView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({"status": "ok"})


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student profile is available only for student accounts."}, status=403)
        return Response(StudentProfileSerializer(get_student_profile(request.user), context={"request": request}).data)

    def patch(self, request):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student profile is available only for student accounts."}, status=403)
        profile = get_student_profile(request.user)
        serializer = StudentProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StudentSkillListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        return Response(StudentSkillSerializer(get_student_profile(request.user).skills.select_related("skill"), many=True).data)

    def post(self, request):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        profile = get_student_profile(request.user)
        serializer = StudentSkillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj, created = StudentSkill.objects.update_or_create(
            student=profile,
            skill=serializer.validated_data["skill"],
            defaults={k: v for k, v in serializer.validated_data.items() if k != "skill"},
        )
        return Response(StudentSkillSerializer(obj).data, status=201 if created else 200)


class StudentSkillDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, pk):
        obj = get_object_or_404(StudentSkill, pk=pk, student=get_student_profile(request.user))
        serializer = StudentSkillSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StudentSkillSerializer(obj).data)

    def delete(self, request, pk):
        obj = get_object_or_404(StudentSkill, pk=pk, student=get_student_profile(request.user))
        obj.delete()
        return Response(status=204)


class SkillCatalogView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(SkillSerializer(Skill.objects.all().order_by("category", "name"), many=True).data)


class StudentDirectoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if request.user.role not in ("ADMIN", "FACULTY"):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        qs = __import__("students.models", fromlist=["StudentProfile"]).StudentProfile.objects.select_related("user").order_by("register_number")
        return Response([{"id": p.id, "user_id": p.user_id, "name": p.user.get_full_name() or p.user.username, "email": p.user.email, "register_number": p.register_number} for p in qs])
