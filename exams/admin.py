from django.contrib import admin
from .models import Exam, Question, Result, ExamSession, Course, Enrollment


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'status', 'start_time', 'end_time', 'duration_minutes']
    list_filter = ['status']
    search_fields = ['title']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'exam', 'question_type', 'marks']
    list_filter = ['question_type', 'exam']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'score', 'total_marks', 'percentage', 'passed', 'submitted_at']
    list_filter = ['passed', 'exam']
    readonly_fields = ['answers_data']


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'started_at', 'expires_at', 'is_submitted']


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ['enrolled_at']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'created_by', 'is_active', 'enrolled_count', 'exam_count']
    list_filter = ['is_active']
    search_fields = ['title', 'code']
    inlines = [EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrolled_by', 'enrolled_at']
    list_filter = ['status', 'course']
