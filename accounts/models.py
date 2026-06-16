from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_STUDENT = 'student'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_ADMIN, 'Admin'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_staff

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
