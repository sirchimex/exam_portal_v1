from django.db import models
from django.utils import timezone
from accounts.models import User
import json


class Exam(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exams')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(help_text='Exam duration in minutes')
    passing_score = models.PositiveIntegerField(default=50, help_text='Minimum passing score (%)')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_attempts = models.PositiveIntegerField(default=1)
    shuffle_questions = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_active(self):
        now = timezone.now()
        return self.status == self.STATUS_PUBLISHED and self.start_time <= now <= self.end_time

    def is_upcoming(self):
        return self.status == self.STATUS_PUBLISHED and timezone.now() < self.start_time

    def total_marks(self):
        return self.questions.aggregate(total=models.Sum('marks'))['total'] or 0

    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    TYPE_MCQ = 'mcq'
    TYPE_SHORT = 'short'
    TYPE_TRUE_FALSE = 'true_false'
    TYPE_CHOICES = [
        (TYPE_MCQ, 'Multiple Choice'),
        (TYPE_SHORT, 'Short Answer'),
        (TYPE_TRUE_FALSE, 'True/False'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default=TYPE_MCQ)
    option_a = models.CharField(max_length=300, blank=True)
    option_b = models.CharField(max_length=300, blank=True)
    option_c = models.CharField(max_length=300, blank=True)
    option_d = models.CharField(max_length=300, blank=True)
    correct_answer = models.CharField(max_length=300)
    explanation = models.TextField(blank=True, help_text='Explanation shown after submission')
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}..."

    def get_options(self):
        if self.question_type == self.TYPE_MCQ:
            opts = []
            for label, val in [('A', self.option_a), ('B', self.option_b),
                                ('C', self.option_c), ('D', self.option_d)]:
                if val:
                    opts.append((label, val))
            return opts
        elif self.question_type == self.TYPE_TRUE_FALSE:
            return [('True', 'True'), ('False', 'False')]
        return []

    def is_correct(self, answer):
        return answer.strip().lower() == self.correct_answer.strip().lower()


class Result(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    score = models.FloatField(default=0)
    total_marks = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    time_taken_minutes = models.FloatField(default=0)
    answers_data = models.JSONField(default=dict)
    attempt_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['student', 'exam', 'attempt_number']

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} ({self.percentage:.1f}%)"

    def save(self, *args, **kwargs):
        if self.total_marks > 0:
            self.percentage = (self.score / self.total_marks) * 100
        self.passed = self.percentage >= self.exam.passing_score
        super().save(*args, **kwargs)


class ExamSession(models.Model):
    """Tracks active exam sessions to prevent cheating and handle timeouts."""
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_submitted = models.BooleanField(default=False)
    temp_answers = models.JSONField(default=dict)

    class Meta:
        unique_together = ['student', 'exam']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def remaining_seconds(self):
        delta = self.expires_at - timezone.now()
        return max(0, int(delta.total_seconds()))


# ─── Course & Enrollment ──────────────────────────────────────────────────────

class Course(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    exams = models.ManyToManyField(Exam, blank=True, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.code}] {self.title}"

    def enrolled_count(self):
        return self.enrollments.filter(status=Enrollment.STATUS_ACTIVE).count()

    def exam_count(self):
        return self.exams.count()


class Enrollment(models.Model):
    STATUS_ACTIVE   = 'active'
    STATUS_DROPPED  = 'dropped'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE,    'Active'),
        (STATUS_DROPPED,   'Dropped'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    student  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course   = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='assigned_enrollments'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    notes  = models.TextField(blank=True)

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} → {self.course.code}"
