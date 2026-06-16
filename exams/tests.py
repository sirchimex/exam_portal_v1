from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from .models import Exam, Question, Result, ExamSession


def make_exam(creator, status='published', offset_hours=0):
    now = timezone.now()
    return Exam.objects.create(
        title='Test Exam',
        created_by=creator,
        start_time=now - timedelta(hours=1) + timedelta(hours=offset_hours),
        end_time=now + timedelta(hours=2),
        duration_minutes=60,
        status=status,
    )


def make_question(exam, qtype='mcq'):
    return Question.objects.create(
        exam=exam, text='What is 2+2?', question_type=qtype,
        option_a='3', option_b='4', option_c='5', option_d='6',
        correct_answer='B', marks=1, order=1
    )


class ExamModelTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='p', role='admin')
        self.exam = make_exam(self.admin)

    def test_is_active(self):
        self.assertTrue(self.exam.is_active())

    def test_is_not_active_when_draft(self):
        self.exam.status = 'draft'
        self.exam.save()
        self.assertFalse(self.exam.is_active())

    def test_question_count(self):
        make_question(self.exam)
        make_question(self.exam)
        self.assertEqual(self.exam.question_count(), 2)

    def test_total_marks(self):
        make_question(self.exam)
        make_question(self.exam)
        self.assertEqual(self.exam.total_marks(), 2)

    def test_str(self):
        self.assertEqual(str(self.exam), 'Test Exam')


class QuestionModelTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a', password='p', role='admin')
        self.exam = make_exam(self.admin)
        self.q = make_question(self.exam)

    def test_is_correct_case_insensitive(self):
        self.assertTrue(self.q.is_correct('b'))
        self.assertTrue(self.q.is_correct('B'))

    def test_is_incorrect(self):
        self.assertFalse(self.q.is_correct('A'))

    def test_get_options_mcq(self):
        opts = self.q.get_options()
        self.assertEqual(len(opts), 4)
        self.assertEqual(opts[0], ('A', '3'))

    def test_get_options_true_false(self):
        q = Question.objects.create(
            exam=self.exam, text='True?', question_type='true_false',
            correct_answer='True', marks=1
        )
        opts = q.get_options()
        self.assertEqual(len(opts), 2)


class ResultModelTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a', password='p', role='admin')
        self.student = User.objects.create_user(username='s', password='p', role='student')
        self.exam = make_exam(self.admin)
        make_question(self.exam)

    def test_result_percentage_and_passed(self):
        result = Result.objects.create(
            student=self.student, exam=self.exam,
            score=1, total_marks=1, attempt_number=1
        )
        self.assertEqual(result.percentage, 100.0)
        self.assertTrue(result.passed)

    def test_result_failed(self):
        result = Result.objects.create(
            student=self.student, exam=self.exam,
            score=0, total_marks=1, attempt_number=1
        )
        self.assertFalse(result.passed)


class ExamViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin', password='p', role='admin')
        self.student = User.objects.create_user(username='student', password='p', role='student')
        self.exam = make_exam(self.admin)
        self.question = make_question(self.exam)

    def test_dashboard_admin(self):
        self.client.login(username='admin', password='p')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'exams/admin_dashboard.html')

    def test_dashboard_student(self):
        self.client.login(username='student', password='p')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'exams/student_dashboard.html')

    def test_exam_list_admin_only(self):
        self.client.login(username='student', password='p')
        r = self.client.get(reverse('exam_list'))
        self.assertRedirects(r, reverse('dashboard'))

    def test_exam_create_admin(self):
        self.client.login(username='admin', password='p')
        r = self.client.get(reverse('exam_create'))
        self.assertEqual(r.status_code, 200)

    def test_available_exams_student(self):
        self.client.login(username='student', password='p')
        r = self.client.get(reverse('available_exams'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Test Exam')

    def test_start_exam_creates_session(self):
        self.client.login(username='student', password='p')
        r = self.client.post(reverse('start_exam', kwargs={'pk': self.exam.pk}))
        self.assertEqual(ExamSession.objects.filter(student=self.student, exam=self.exam).count(), 1)

    def test_take_exam_requires_session(self):
        self.client.login(username='student', password='p')
        r = self.client.get(reverse('take_exam', kwargs={'pk': self.exam.pk}))
        self.assertEqual(r.status_code, 404)

    def test_exam_submission(self):
        self.client.login(username='student', password='p')
        self.client.post(reverse('start_exam', kwargs={'pk': self.exam.pk}))
        r = self.client.post(reverse('take_exam', kwargs={'pk': self.exam.pk}), {
            f'question_{self.question.pk}': 'B',
        })
        result = Result.objects.filter(student=self.student, exam=self.exam).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.score, 1.0)
        self.assertTrue(result.passed)


# ─── Course & Enrollment Tests ────────────────────────────────────────────────

from .models import Course, Enrollment


def make_course(admin, title='Intro to Python', code='CS101'):
    return Course.objects.create(
        title=title, code=code,
        created_by=admin, is_active=True
    )


class CourseModelTest(TestCase):
    def setUp(self):
        self.admin   = User.objects.create_user(username='ca', password='p', role='admin')
        self.student = User.objects.create_user(username='cs', password='p', role='student')
        self.course  = make_course(self.admin)

    def test_str(self):
        self.assertIn('CS101', str(self.course))

    def test_enrolled_count_zero(self):
        self.assertEqual(self.course.enrolled_count(), 0)

    def test_enrolled_count_after_enroll(self):
        Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_ACTIVE
        )
        self.assertEqual(self.course.enrolled_count(), 1)

    def test_enrolled_count_excludes_dropped(self):
        Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_DROPPED
        )
        self.assertEqual(self.course.enrolled_count(), 0)

    def test_exam_count(self):
        admin2 = User.objects.create_user(username='ca2', password='p', role='admin')
        exam = make_exam(admin2)
        self.course.exams.add(exam)
        self.assertEqual(self.course.exam_count(), 1)


class CourseViewsTest(TestCase):
    def setUp(self):
        self.client  = Client()
        self.admin   = User.objects.create_user(username='va', password='p', role='admin')
        self.student = User.objects.create_user(username='vs', password='p', role='student')
        self.course  = make_course(self.admin)

    # ── Admin views ──────────────────────────────────────────────────────────

    def test_course_list_requires_admin(self):
        self.client.login(username='vs', password='p')
        r = self.client.get(reverse('course_list'))
        self.assertRedirects(r, reverse('dashboard'))

    def test_course_list_admin_ok(self):
        self.client.login(username='va', password='p')
        r = self.client.get(reverse('course_list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Intro to Python')

    def test_course_create_get(self):
        self.client.login(username='va', password='p')
        r = self.client.get(reverse('course_create'))
        self.assertEqual(r.status_code, 200)

    def test_course_create_post(self):
        self.client.login(username='va', password='p')
        r = self.client.post(reverse('course_create'), {
            'title': 'Advanced Django', 'code': 'DJ301',
            'description': 'Deep-dive into Django.', 'is_active': 'on',
        })
        self.assertTrue(Course.objects.filter(code='DJ301').exists())
        self.assertRedirects(r, reverse('course_list'))

    def test_course_detail_shows_enrollments(self):
        Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_ACTIVE
        )
        self.client.login(username='va', password='p')
        r = self.client.get(reverse('course_detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.student.username)

    def test_enroll_students(self):
        self.client.login(username='va', password='p')
        r = self.client.post(reverse('course_enroll', kwargs={'pk': self.course.pk}), {
            'students': [self.student.pk],
            'notes': 'Test enrolment',
        })
        self.assertRedirects(r, reverse('course_detail', kwargs={'pk': self.course.pk}))
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student, course=self.course, status=Enrollment.STATUS_ACTIVE
            ).exists()
        )

    def test_enroll_duplicate_reactivates(self):
        """Enrolling a dropped student reactivates them."""
        enr = Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_DROPPED
        )
        self.client.login(username='va', password='p')
        self.client.post(reverse('course_enroll', kwargs={'pk': self.course.pk}), {
            'students': [self.student.pk],
        })
        enr.refresh_from_db()
        self.assertEqual(enr.status, Enrollment.STATUS_ACTIVE)

    def test_unenroll_student(self):
        enr = Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_ACTIVE
        )
        self.client.login(username='va', password='p')
        self.client.post(reverse('course_unenroll', kwargs={
            'pk': self.course.pk, 'enrollment_pk': enr.pk
        }))
        enr.refresh_from_db()
        self.assertEqual(enr.status, Enrollment.STATUS_DROPPED)

    # ── Student views ─────────────────────────────────────────────────────────

    def test_my_courses_requires_student(self):
        self.client.login(username='va', password='p')
        r = self.client.get(reverse('my_courses'))
        self.assertRedirects(r, reverse('dashboard'))

    def test_my_courses_empty(self):
        self.client.login(username='vs', password='p')
        r = self.client.get(reverse('my_courses'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'No courses yet')

    def test_my_courses_shows_enrolled(self):
        Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_ACTIVE
        )
        self.client.login(username='vs', password='p')
        r = self.client.get(reverse('my_courses'))
        self.assertContains(r, 'Intro to Python')

    def test_my_course_detail_access_denied_unenrolled(self):
        self.client.login(username='vs', password='p')
        r = self.client.get(reverse('my_course_detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 404)

    def test_my_course_detail_enrolled_ok(self):
        Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_ACTIVE
        )
        self.client.login(username='vs', password='p')
        r = self.client.get(reverse('my_course_detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Intro to Python')

    def test_dropped_student_cannot_view_course(self):
        Enrollment.objects.create(
            student=self.student, course=self.course,
            enrolled_by=self.admin, status=Enrollment.STATUS_DROPPED
        )
        self.client.login(username='vs', password='p')
        r = self.client.get(reverse('my_course_detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(r.status_code, 404)

    def test_course_delete(self):
        self.client.login(username='va', password='p')
        r = self.client.post(reverse('course_delete', kwargs={'pk': self.course.pk}))
        self.assertRedirects(r, reverse('course_list'))
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())
