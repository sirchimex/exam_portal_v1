from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from exams.models import Exam, Question, Result, ExamSession, Course, Enrollment


class Command(BaseCommand):
    help = 'Seed the database with demo data'

    def handle(self, *args, **kwargs):
        User.objects.filter(username__in=['admin', 'student', 'student2']).delete()

        now = timezone.now()

        admin = User.objects.create_superuser(
            username='admin', password='admin123',
            email='admin@examportal.com',
            first_name='Admin', last_name='User', role='admin'
        )
        student = User.objects.create_user(
            username='student', password='student123',
            email='alice@example.com',
            first_name='Alice', last_name='Johnson',
            role='student', institution='State University'
        )
        student2 = User.objects.create_user(
            username='student2', password='student123',
            email='bob@example.com',
            first_name='Bob', last_name='Smith',
            role='student', institution='City College'
        )

        # ── Exams ──────────────────────────────────────────────────────────────
        exam1 = Exam.objects.create(
            title='Python Fundamentals',
            description='Test your knowledge of core Python concepts.',
            instructions='Read each question carefully. You have 30 minutes.',
            created_by=admin,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=23),
            duration_minutes=30, passing_score=60, status='published',
        )
        for q in [
            dict(text='What is the output of print(type([]))?', question_type='mcq',
                 option_a="<class 'list'>", option_b="<class 'array'>",
                 option_c='list', option_d='Array',
                 correct_answer='A', explanation="[] is a list literal.", marks=2, order=1),
            dict(text='Which keyword defines a function in Python?', question_type='mcq',
                 option_a='function', option_b='def', option_c='fun', option_d='define',
                 correct_answer='B', explanation='def keyword.', marks=1, order=2),
            dict(text='Python is a compiled language.', question_type='true_false',
                 correct_answer='False', explanation='Python is interpreted.', marks=1, order=3),
            dict(text='What does len("hello") return?', question_type='mcq',
                 option_a='4', option_b='5', option_c='6', option_d='None',
                 correct_answer='B', marks=1, order=4),
            dict(text='Python single-line comment symbol?', question_type='mcq',
                 option_a='//', option_b='--', option_c='#', option_d='/*',
                 correct_answer='C', marks=1, order=5),
            dict(text='Describe a list comprehension briefly.', question_type='short',
                 correct_answer='A concise way to create lists',
                 explanation='e.g. [x*2 for x in range(5)]', marks=2, order=6),
        ]:
            Question.objects.create(exam=exam1, **q)

        exam2 = Exam.objects.create(
            title='Data Structures & Algorithms',
            description='MCQ covering arrays, linked lists, sorting, searching.',
            created_by=admin,
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=3),
            duration_minutes=60, passing_score=70, status='published',
        )

        exam3 = Exam.objects.create(
            title='Web Development Basics',
            description='HTML, CSS, and HTTP fundamentals.',
            created_by=admin,
            start_time=now - timedelta(hours=2),
            end_time=now + timedelta(hours=10),
            duration_minutes=45, passing_score=65, status='published',
        )
        for q in [
            dict(text='What does HTML stand for?', question_type='mcq',
                 option_a='Hyper Text Markup Language',
                 option_b='High Tech Modern Language',
                 option_c='Hyper Transfer Markup Language',
                 option_d='Hyperlink Text Management Language',
                 correct_answer='A', marks=1, order=1),
            dict(text='Which CSS property changes text colour?', question_type='mcq',
                 option_a='font-color', option_b='text-color',
                 option_c='color', option_d='foreground',
                 correct_answer='C', marks=1, order=2),
            dict(text='HTTP stands for HyperText Transfer Protocol.', question_type='true_false',
                 correct_answer='True', marks=1, order=3),
        ]:
            Question.objects.create(exam=exam3, **q)

        # ── Courses ────────────────────────────────────────────────────────────
        cs_course = Course.objects.create(
            title='Computer Science Fundamentals',
            code='CS101',
            description='An introduction to programming and core CS concepts.',
            created_by=admin, is_active=True,
        )
        cs_course.exams.set([exam1, exam2])

        web_course = Course.objects.create(
            title='Web Development Bootcamp',
            code='WEB201',
            description='Full-stack web development from the ground up.',
            created_by=admin, is_active=True,
        )
        web_course.exams.set([exam3])

        # ── Enrolments ─────────────────────────────────────────────────────────
        Enrollment.objects.create(
            student=student, course=cs_course,
            enrolled_by=admin, status=Enrollment.STATUS_ACTIVE,
            notes='Enrolled for Semester 1'
        )
        Enrollment.objects.create(
            student=student, course=web_course,
            enrolled_by=admin, status=Enrollment.STATUS_ACTIVE,
        )
        Enrollment.objects.create(
            student=student2, course=cs_course,
            enrolled_by=admin, status=Enrollment.STATUS_ACTIVE,
        )

        self.stdout.write(self.style.SUCCESS(
            '\nDemo data seeded successfully!\n'
            '─────────────────────────────────────────\n'
            '  Admin   → username: admin    password: admin123\n'
            '  Student → username: student  password: student123\n'
            '  Student → username: student2 password: student123\n'
            '─────────────────────────────────────────\n'
            f'  {Exam.objects.count()} exams · '
            f'{Course.objects.count()} courses · '
            f'{Enrollment.objects.count()} enrollments'
        ))
