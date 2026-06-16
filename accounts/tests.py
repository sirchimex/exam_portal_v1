from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class UserModelTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='teststudent', password='pass1234', role='student',
            first_name='Alice', last_name='Smith'
        )
        self.admin = User.objects.create_user(
            username='testadmin', password='pass1234', role='admin'
        )

    def test_student_role(self):
        self.assertTrue(self.student.is_student())
        self.assertFalse(self.student.is_admin_user())

    def test_admin_role(self):
        self.assertFalse(self.admin.is_student())
        self.assertTrue(self.admin.is_admin_user())

    def test_str(self):
        self.assertIn('student', str(self.student))

    def test_full_name(self):
        self.assertEqual(self.student.get_full_name(), 'Alice Smith')


class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='u', password='p', role='student')

    def test_login_page_loads(self):
        r = self.client.get(reverse('login'))
        self.assertEqual(r.status_code, 200)

    def test_register_page_loads(self):
        r = self.client.get(reverse('register'))
        self.assertEqual(r.status_code, 200)

    def test_login_success_redirects(self):
        r = self.client.post(reverse('login'), {'username': 'u', 'password': 'p'})
        self.assertRedirects(r, reverse('dashboard'))

    def test_login_redirects_if_already_logged_in(self):
        self.client.login(username='u', password='p')
        r = self.client.get(reverse('login'))
        self.assertRedirects(r, reverse('dashboard'))

    def test_profile_requires_login(self):
        r = self.client.get(reverse('profile'))
        self.assertRedirects(r, '/accounts/login/?next=/accounts/profile/')
