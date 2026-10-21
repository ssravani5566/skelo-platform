from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import IsFacultyOrAdmin
from students.services import get_student_profile
from .models import Course, CourseModule, Lesson, CourseProgress
from .serializers import CourseModuleSerializer, CourseProgressSerializer, CourseSerializer, LessonSerializer
from .services import complete_lesson, start_course
from core.api import paginated_response


class HealthView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return Response({"status": "ok"})


class CourseListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        qs = Course.objects.prefetch_related("modules__lessons").all()
        if request.user.role == "STUDENT": qs = qs.filter(is_published=True)
        else:
            if request.query_params.get("published") in {"true", "false"}:
                qs = qs.filter(is_published=request.query_params["published"] == "true")
        q = request.query_params.get("q", "").strip()
        if q: qs = qs.filter(Q(title__icontains=q) | Q(category__icontains=q) | Q(description__icontains=q))
        level = request.query_params.get("level")
        if level: qs = qs.filter(level=level.upper())
        data = CourseSerializer(qs.order_by("title"), many=True, context={"request": request, "student": get_student_profile(request.user) if request.user.role == "STUDENT" else None}).data
        from core.api import paginated_response
        # paginate serialized data without re-running context lookups
        return paginated_response(request, data)

    def post(self, request):
        if request.user.role not in ("ADMIN", "FACULTY"):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        from rest_framework import serializers
        serializer = CourseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(created_by=request.user)
        return Response(CourseSerializer(obj, context={"request": request}).data, status=201)


class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        qs = Course.objects.prefetch_related("modules__lessons")
        if request.user.role == "STUDENT": qs = qs.filter(is_published=True)
        course = get_object_or_404(qs, pk=pk)
        return Response(CourseSerializer(course, context={"request": request, "student": get_student_profile(request.user) if request.user.role == "STUDENT" else None}).data)

    def patch(self, request, pk):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=pk)
        if request.user.role == "FACULTY" and course.created_by_id not in (None, request.user.id):
            return Response({"detail": "You can edit only your courses."}, status=403)
        serializer = CourseSerializer(course, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True); serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=pk)
        course.delete(); return Response(status=204)


class CourseModulesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id, **({"is_published": True} if request.user.role == "STUDENT" else {}))
        student = get_student_profile(request.user) if request.user.role == "STUDENT" else None
        return Response(CourseModuleSerializer(course.modules.all(), many=True, context={"request": request, "student": student}).data)
    def post(self, request, course_id):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail":"Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=course_id)
        serializer = CourseModuleSerializer(data={**request.data, "course": course.id}, context={"request": request}); serializer.is_valid(raise_exception=True); obj=serializer.save(); return Response(CourseModuleSerializer(obj).data, status=201)
    def patch(self, request, course_id):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail":"Faculty or admin access required."}, status=403)
        obj=get_object_or_404(CourseModule,pk=request.data.get("id"),course_id=course_id)
        serializer=CourseModuleSerializer(obj,data=request.data,partial=True,context={"request":request}); serializer.is_valid(raise_exception=True); serializer.save(); return Response(serializer.data)
    def delete(self, request, course_id):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail":"Faculty or admin access required."}, status=403)
        get_object_or_404(CourseModule,pk=request.data.get("id"),course_id=course_id).delete(); return Response(status=204)


class LessonsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, course_id):
        qs = Lesson.objects.filter(module__course_id=course_id, is_published=True).select_related("module")
        student = get_student_profile(request.user) if request.user.role == "STUDENT" else None
        return Response(LessonSerializer(qs, many=True, context={"request": request, "student": student}).data)

    def post(self, request, course_id):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail":"Faculty or admin access required."}, status=403)
        module_id = request.data.get("module") or request.data.get("module_id")
        module = get_object_or_404(CourseModule, pk=module_id, course_id=course_id)
        serializer = LessonSerializer(data={**request.data, "module": module.id}, context={"request": request}); serializer.is_valid(raise_exception=True); obj=serializer.save(); return Response(LessonSerializer(obj).data, status=201)
    def patch(self, request, course_id):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail":"Faculty or admin access required."}, status=403)
        obj=get_object_or_404(Lesson,pk=request.data.get("id"),module__course_id=course_id)
        serializer=LessonSerializer(obj,data=request.data,partial=True,context={"request":request}); serializer.is_valid(raise_exception=True); serializer.save(); return Response(serializer.data)
    def delete(self, request, course_id):
        if request.user.role not in ("ADMIN", "FACULTY"): return Response({"detail":"Faculty or admin access required."}, status=403)
        get_object_or_404(Lesson,pk=request.data.get("id"),module__course_id=course_id).delete(); return Response(status=204)


class CourseStartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        if request.user.role != "STUDENT": return Response({"detail":"Student access required."}, status=403)
        course = get_object_or_404(Course, pk=pk, is_published=True)
        return Response(CourseProgressSerializer(start_course(get_student_profile(request.user), course)).data)


class LessonCompleteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        if request.user.role != "STUDENT": return Response({"detail":"Student access required."}, status=403)
        lesson = get_object_or_404(Lesson, pk=pk, is_published=True)
        profile = get_student_profile(request.user)
        if not Course.objects.filter(pk=lesson.module.course_id, is_published=True).exists(): return Response({"detail":"Course is not available."}, status=404)
        complete_lesson(profile, lesson)
        return Response(LessonSerializer(lesson, context={"request": request, "student": profile}).data)


class MyCourseProgressView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if request.user.role != "STUDENT": return Response({"detail":"Student access required."}, status=403)
        qs = CourseProgress.objects.filter(student=get_student_profile(request.user)).select_related("course")
        return Response(CourseProgressSerializer(qs, many=True).data)
