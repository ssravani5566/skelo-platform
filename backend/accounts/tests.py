from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from assessments.models import Assessment, AssessmentQuestion, Question
from assignments.models import Assignment
from coding.models import Problem, TestCase as CodingTestCase
from coding.services import evaluate_submission
from courses.models import Course, CourseModule, Lesson, CourseProgress, LessonProgress
from notifications.models import Notification
from reports.services import report_overview
from students.services import get_student_profile
from students.models import StudentProfile


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class StudentPlatformIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "StrongPass123!"
        self.student = User.objects.create_user(
            username="student1", email="student1@example.com", password=self.password,
            first_name="Test", last_name="Student", role=User.ROLE_STUDENT,
        )
        self.faculty = User.objects.create_user(
            username="faculty1", email="faculty1@example.com", password=self.password,
            role=User.ROLE_FACULTY,
        )

    def authenticate(self, user=None):
        user = user or self.student
        response = self.client.post("/api/auth/login/", {"email": user.email, "password": self.password}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data

    def test_public_registration_forces_student_and_creates_profile(self):
        response = self.client.post(
            "/api/auth/register/",
            {"username": "newstudent", "email": "newstudent@example.com", "password": self.password, "role": "ADMIN"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created = User.objects.get(email="newstudent@example.com")
        self.assertEqual(created.role, User.ROLE_STUDENT)
        self.assertTrue(StudentProfile.objects.filter(user=created).exists())
        self.assertTrue(created.student_profile.register_number.startswith("STU"))
        self.assertEqual(len(mail.outbox), 1)

    def test_profile_patch_persists_to_database(self):
        self.authenticate()
        response = self.client.patch("/api/auth/profile/", {"college": "SCOTT College", "department": "CSE", "year": 3}, format="multipart")
        self.assertEqual(response.status_code, 200)
        profile = StudentProfile.objects.get(user=self.student)
        self.assertEqual(profile.college, "SCOTT College")
        self.assertEqual(profile.department, "CSE")
        self.assertEqual(profile.year, 3)

    def test_course_completion_is_persisted_and_report_reads_it(self):
        course = Course.objects.create(title="Python", slug="python", description="Learn Python", is_published=True, created_by=self.faculty)
        module = CourseModule.objects.create(course=course, title="Basics", order=1)
        lesson = Lesson.objects.create(module=module, title="Variables", content="x = 1", order=1, is_published=True)
        self.authenticate()
        start = self.client.post(f"/api/courses/{course.id}/start/")
        self.assertEqual(start.status_code, 200)
        done = self.client.post(f"/api/courses/lessons/{lesson.id}/complete/")
        self.assertEqual(done.status_code, 200)
        progress = CourseProgress.objects.get(student=self.student.student_profile, course=course)
        self.assertEqual(float(progress.percentage), 100.0)
        self.assertTrue(progress.completed)
        self.assertTrue(LessonProgress.objects.filter(student=self.student.student_profile, lesson=lesson, completed=True).exists())
        report = report_overview(self.student)
        self.assertEqual(report["course_completion"], 100.0)

    def test_coding_submission_evaluates_and_awards_xp_once(self):
        problem = Problem.objects.create(title="Add", slug="add", description="Print 2", points=20, is_published=True)
        CodingTestCase.objects.create(problem=problem, input_data="", expected_output="2", is_sample=True, order=1)
        submission1 = evaluate_submission(get_student_profile(self.student), problem, "PYTHON", "print(2)")
        self.assertEqual(submission1.status, "ACCEPTED")
        submission2 = evaluate_submission(get_student_profile(self.student), problem, "PYTHON", "print(2)")
        self.assertEqual(submission2.status, "ACCEPTED")
        self.assertEqual(get_student_profile(self.student).xp_transactions.filter(source_key=f"problem:{problem.id}").count(), 1)

    def test_assessment_hides_answers_and_persists_result(self):
        assessment = Assessment.objects.create(title="Python Test", is_published=True, total_marks=5, passing_marks=3, created_by=self.faculty)
        question = Question.objects.create(text="2+2?", question_type="MCQ", option_a="3", option_b="4", correct_answer="B", marks=5, explanation="Arithmetic")
        AssessmentQuestion.objects.create(assessment=assessment, question=question, marks=5, order=1)
        self.authenticate()
        detail = self.client.get(f"/api/assessments/{assessment.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertNotIn("correct_answer", detail.data["questions_data"][0])
        attempt = self.client.post(f"/api/assessments/{assessment.id}/start/", format="json")
        self.assertEqual(attempt.status_code, 200)
        attempt_id = attempt.data["id"]
        answered = self.client.post(f"/api/assessments/attempts/{attempt_id}/answer/", {"question": question.id, "answer_text": "B"}, format="json")
        self.assertEqual(answered.status_code, 200)
        submitted = self.client.post(f"/api/assessments/attempts/{attempt_id}/submit/", format="json")
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(float(submitted.data["percentage"]), 100.0)

    def test_assignment_submission_and_evaluation_are_user_scoped(self):
        assignment = Assignment.objects.create(title="Task", description="Do it", due_date="2030-01-01T10:00:00Z", max_marks=100, status="PUBLISHED", created_by=self.faculty)
        self.authenticate()
        response = self.client.post(f"/api/assignments/{assignment.id}/submit/", {"answer_text": "done"}, format="multipart")
        self.assertEqual(response.status_code, 200)
        submission_id = response.data["id"]
        faculty_client = APIClient()
        faculty_response = faculty_client.post("/api/auth/login/", {"email": self.faculty.email, "password": self.password}, format="json")
        faculty_client.credentials(HTTP_AUTHORIZATION=f"Bearer {faculty_response.data['access']}")
        evaluated = faculty_client.post(f"/api/assignments/submissions/{submission_id}/", {"marks": 90, "feedback": "Good"}, format="json")
        self.assertEqual(evaluated.status_code, 200)
        notification = Notification.objects.filter(recipient=self.student, title="Assignment evaluated").first()
        self.assertIsNotNone(notification)
        other = User.objects.create_user(username="other", email="other@example.com", password=self.password, role=User.ROLE_STUDENT)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.authenticate(other)['access']}")
        forbidden = self.client.get(f"/api/assignments/submissions/{submission_id}/")
        self.assertEqual(forbidden.status_code, 404)
