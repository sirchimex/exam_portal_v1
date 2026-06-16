from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
import json

from .models import Exam, Question, Result, ExamSession, Course, Enrollment
from .forms import ExamForm, QuestionForm, QuestionFormSet, CourseForm, EnrollStudentsForm
from .mixins import AdminRequiredMixin, StudentRequiredMixin
from accounts.models import User


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        if self.request.user.is_admin_user():
            return ['exams/admin_dashboard.html']
        return ['exams/student_dashboard.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_admin_user():
            ctx['exams'] = Exam.objects.filter(created_by=user).annotate(
                result_count=Count('results')
            )
            ctx['total_students'] = User.objects.filter(role='student').count()
            ctx['total_exams'] = Exam.objects.filter(created_by=user).count()
            ctx['total_results'] = Result.objects.filter(exam__created_by=user).count()
            ctx['total_courses'] = Course.objects.filter(created_by=user).count()
            ctx['recent_results'] = Result.objects.filter(
                exam__created_by=user).select_related('student', 'exam').order_by('-submitted_at')[:10]
            ctx['recent_courses'] = Course.objects.filter(created_by=user).annotate(
                enrolled_students=Count('enrollments', filter=Q(enrollments__status='active'))
            ).order_by('-created_at')[:5]
        else:
            now = timezone.now()
            ctx['available_exams'] = Exam.objects.filter(
                status='published', start_time__lte=now, end_time__gte=now
            )
            ctx['upcoming_exams'] = Exam.objects.filter(
                status='published', start_time__gt=now
            )
            ctx['results'] = Result.objects.filter(student=user).select_related('exam').order_by('-submitted_at')[:5]
            ctx['total_exams_taken'] = Result.objects.filter(student=user).count()
            ctx['avg_score'] = Result.objects.filter(student=user).aggregate(avg=Avg('percentage'))['avg'] or 0
            ctx['passed_count'] = Result.objects.filter(student=user, passed=True).count()
            ctx['my_courses'] = Enrollment.objects.filter(
                student=user, status=Enrollment.STATUS_ACTIVE
            ).select_related('course').order_by('-enrolled_at')[:4]
        return ctx


# ─── Admin Exam CRUD ──────────────────────────────────────────────────────────

class ExamListView(AdminRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'

    def get_queryset(self):
        return Exam.objects.filter(created_by=self.request.user).annotate(
            result_count=Count('results'),
            question_count=Count('questions')
        )


class ExamCreateView(AdminRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Exam "{self.object.title}" created successfully.')
        return response

    def get_success_url(self):
        return reverse('exam_questions', kwargs={'pk': self.object.pk})


class ExamUpdateView(AdminRequiredMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')

    def get_queryset(self):
        return Exam.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Exam updated successfully.')
        return super().form_valid(form)


class ExamDeleteView(AdminRequiredMixin, DeleteView):
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    success_url = reverse_lazy('exam_list')

    def get_queryset(self):
        return Exam.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Exam deleted.')
        return super().form_valid(form)


# ─── Question Management ───────────────────────────────────────────────────────

class ExamQuestionsView(AdminRequiredMixin, View):
    template_name = 'exams/exam_questions.html'

    def get_exam(self, pk):
        return get_object_or_404(Exam, pk=pk, created_by=self.request.user)

    def get(self, request, pk):
        from django.shortcuts import render
        exam = self.get_exam(pk)
        formset = QuestionFormSet(instance=exam)
        return render(request, self.template_name, {'exam': exam, 'formset': formset})

    def post(self, request, pk):
        from django.shortcuts import render
        exam = self.get_exam(pk)
        formset = QuestionFormSet(request.POST, instance=exam)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Questions saved.')
            return redirect('exam_questions', pk=exam.pk)
        return render(request, self.template_name, {'exam': exam, 'formset': formset})


class QuestionCreateView(AdminRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'exams/question_form.html'

    def get_exam(self):
        return get_object_or_404(Exam, pk=self.kwargs['exam_pk'], created_by=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['exam'] = self.get_exam()
        return ctx

    def form_valid(self, form):
        form.instance.exam = self.get_exam()
        messages.success(self.request, 'Question added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('exam_questions', kwargs={'pk': self.kwargs['exam_pk']})


class QuestionUpdateView(AdminRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'exams/question_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['exam'] = self.object.exam
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Question updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('exam_questions', kwargs={'pk': self.object.exam.pk})


class QuestionDeleteView(AdminRequiredMixin, DeleteView):
    model = Question
    template_name = 'exams/question_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, 'Question deleted.')
        return reverse('exam_questions', kwargs={'pk': self.object.exam.pk})


# ─── Student Exam Taking ───────────────────────────────────────────────────────

class AvailableExamsView(StudentRequiredMixin, ListView):
    template_name = 'exams/available_exams.html'
    context_object_name = 'exams'

    def get_queryset(self):
        now = timezone.now()
        return Exam.objects.filter(
            status='published',
            start_time__lte=now,
            end_time__gte=now
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.request.user
        taken_exam_ids = Result.objects.filter(student=student).values_list('exam_id', flat=True)
        ctx['taken_exam_ids'] = list(taken_exam_ids)
        return ctx


class ExamDetailView(LoginRequiredMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'

    def get_queryset(self):
        return Exam.objects.filter(status='published')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.request.user
        ctx['already_taken'] = Result.objects.filter(student=student, exam=self.object).exists()
        ctx['can_take'] = self.object.is_active() and not ctx['already_taken']
        return ctx


class StartExamView(StudentRequiredMixin, View):
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk, status='published')

        if not exam.is_active():
            messages.error(request, 'This exam is not currently active.')
            return redirect('exam_detail', pk=pk)

        already_taken = Result.objects.filter(student=request.user, exam=exam).count()
        if already_taken >= exam.max_attempts:
            messages.error(request, 'You have already used all attempts for this exam.')
            return redirect('exam_detail', pk=pk)

        session, created = ExamSession.objects.get_or_create(
            student=request.user,
            exam=exam,
            defaults={
                'expires_at': timezone.now() + timezone.timedelta(minutes=exam.duration_minutes)
            }
        )

        if not created and session.is_submitted:
            messages.error(request, 'This exam session is already submitted.')
            return redirect('exam_detail', pk=pk)

        if session.is_expired() and not session.is_submitted:
            session.delete()
            session = ExamSession.objects.create(
                student=request.user,
                exam=exam,
                expires_at=timezone.now() + timezone.timedelta(minutes=exam.duration_minutes)
            )

        return redirect('take_exam', pk=pk)


class TakeExamView(StudentRequiredMixin, View):
    def get(self, request, pk):
        from django.shortcuts import render
        exam = get_object_or_404(Exam, pk=pk, status='published')
        session = get_object_or_404(ExamSession, student=request.user, exam=exam, is_submitted=False)

        if session.is_expired():
            return self._auto_submit(request, session, exam)

        questions = list(exam.questions.all())
        if exam.shuffle_questions:
            import random
            random.shuffle(questions)

        return render(request, 'exams/take_exam.html', {
            'exam': exam,
            'questions': questions,
            'session': session,
            'remaining_seconds': session.remaining_seconds(),
            'saved_answers': session.temp_answers,
        })

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk, status='published')
        session = get_object_or_404(ExamSession, student=request.user, exam=exam)

        if session.is_submitted:
            result = Result.objects.filter(student=request.user, exam=exam).first()
            if result:
                return redirect('exam_result', pk=result.pk)
            return redirect('dashboard')

        return self._process_submission(request, session, exam)

    def _auto_submit(self, request, session, exam):
        return self._process_submission(request, session, exam, auto=True)

    def _process_submission(self, request, session, exam, auto=False):
        answers = {}
        if not auto:
            for key, val in request.POST.items():
                if key.startswith('question_'):
                    q_id = key.replace('question_', '')
                    answers[q_id] = val

        score = 0
        total = 0
        answers_data = {}

        for question in exam.questions.all():
            total += question.marks
            q_id = str(question.pk)
            given = answers.get(q_id, session.temp_answers.get(q_id, ''))
            is_correct = question.is_correct(given) if given else False
            if is_correct:
                score += question.marks
            answers_data[q_id] = {
                'given': given,
                'correct': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation,
                'marks': question.marks,
                'question_text': question.text,
            }

        attempt_number = Result.objects.filter(student=request.user, exam=exam).count() + 1
        time_taken = (timezone.now() - session.started_at).total_seconds() / 60

        result = Result.objects.create(
            student=request.user,
            exam=exam,
            score=score,
            total_marks=total,
            time_taken_minutes=round(time_taken, 2),
            answers_data=answers_data,
            attempt_number=attempt_number,
        )

        session.is_submitted = True
        session.save()

        if auto:
            messages.warning(request, 'Time expired! Your exam was auto-submitted.')
        else:
            messages.success(request, 'Exam submitted successfully!')

        return redirect('exam_result', pk=result.pk)


class SaveAnswerView(StudentRequiredMixin, View):
    """AJAX endpoint for auto-saving answers."""
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        session = get_object_or_404(ExamSession, student=request.user, exam=exam, is_submitted=False)

        if session.is_expired():
            return JsonResponse({'status': 'expired'})

        try:
            data = json.loads(request.body)
            q_id = str(data.get('question_id'))
            answer = data.get('answer', '')
            session.temp_answers[q_id] = answer
            session.save(update_fields=['temp_answers'])
            return JsonResponse({'status': 'saved'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─── Results ──────────────────────────────────────────────────────────────────

class ExamResultView(LoginRequiredMixin, DetailView):
    model = Result
    template_name = 'exams/exam_result.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return Result.objects.all()
        return Result.objects.filter(student=user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        result = self.object
        ctx['answers'] = result.answers_data
        ctx['questions'] = {str(q.pk): q for q in result.exam.questions.all()}
        return ctx


class StudentResultsView(StudentRequiredMixin, ListView):
    template_name = 'exams/student_results.html'
    context_object_name = 'results'

    def get_queryset(self):
        return Result.objects.filter(student=self.request.user).select_related('exam')


class AdminResultsView(AdminRequiredMixin, ListView):
    template_name = 'exams/admin_results.html'
    context_object_name = 'results'

    def get_queryset(self):
        qs = Result.objects.filter(exam__created_by=self.request.user).select_related('student', 'exam')
        exam_pk = self.request.GET.get('exam')
        if exam_pk:
            qs = qs.filter(exam__pk=exam_pk)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['exams'] = Exam.objects.filter(created_by=self.request.user)
        ctx['selected_exam'] = self.request.GET.get('exam', '')
        return ctx


# ─── Course Management (Admin) ────────────────────────────────────────────────


class CourseListView(AdminRequiredMixin, ListView):
    model = Course
    template_name = 'exams/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(created_by=self.request.user).annotate(
            enrolled_students=Count('enrollments', filter=Q(enrollments__status='active')),
            total_exams=Count('exams'),
        )


class CourseCreateView(AdminRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'exams/course_form.html'
    success_url = reverse_lazy('course_list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['admin_user'] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Course "{form.instance.title}" created.')
        return super().form_valid(form)


class CourseUpdateView(AdminRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'exams/course_form.html'
    success_url = reverse_lazy('course_list')

    def get_queryset(self):
        return Course.objects.filter(created_by=self.request.user)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['admin_user'] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, 'Course updated.')
        return super().form_valid(form)


class CourseDeleteView(AdminRequiredMixin, DeleteView):
    model = Course
    template_name = 'exams/course_confirm_delete.html'
    success_url = reverse_lazy('course_list')

    def get_queryset(self):
        return Course.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Course deleted.')
        return super().form_valid(form)


class CourseDetailView(AdminRequiredMixin, DetailView):
    model = Course
    template_name = 'exams/course_detail.html'

    def get_queryset(self):
        return Course.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['enrollments'] = self.object.enrollments.select_related('student').order_by('-enrolled_at')
        ctx['enroll_form'] = EnrollStudentsForm(course=self.object)
        return ctx


class EnrollStudentsView(AdminRequiredMixin, View):
    """POST: bulk-enrol students into a course."""

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk, created_by=request.user)
        form = EnrollStudentsForm(request.POST, course=course)
        if form.is_valid():
            students = form.cleaned_data['students']
            notes    = form.cleaned_data.get('notes', '')
            count = 0
            for student in students:
                _, created = Enrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'enrolled_by': request.user,
                        'notes': notes,
                        'status': Enrollment.STATUS_ACTIVE,
                    }
                )
                if not created:
                    # Re-activate if previously dropped
                    Enrollment.objects.filter(student=student, course=course).update(
                        status=Enrollment.STATUS_ACTIVE,
                        enrolled_by=request.user,
                        notes=notes,
                    )
                count += 1
            messages.success(request, f'{count} student(s) enrolled in "{course.title}".')
        else:
            messages.error(request, 'Please select at least one student.')
        return redirect('course_detail', pk=pk)


class UnenrollStudentView(AdminRequiredMixin, View):
    """POST: drop a single student from a course."""

    def post(self, request, pk, enrollment_pk):
        course     = get_object_or_404(Course, pk=pk, created_by=request.user)
        enrollment = get_object_or_404(Enrollment, pk=enrollment_pk, course=course)
        name = enrollment.student.get_full_name() or enrollment.student.username
        enrollment.status = Enrollment.STATUS_DROPPED
        enrollment.save(update_fields=['status'])
        messages.success(request, f'{name} has been removed from "{course.title}".')
        return redirect('course_detail', pk=pk)


# ─── Student: My Courses ──────────────────────────────────────────────────────

class MyCoursesView(StudentRequiredMixin, ListView):
    template_name = 'exams/my_courses.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return (
            Enrollment.objects
            .filter(student=self.request.user, status=Enrollment.STATUS_ACTIVE)
            .select_related('course')
            .prefetch_related('course__exams')
            .order_by('-enrolled_at')
        )


class MyCourseDetailView(StudentRequiredMixin, DetailView):
    template_name = 'exams/my_course_detail.html'

    def get_object(self):
        return get_object_or_404(
            Course,
            pk=self.kwargs['pk'],
            enrollments__student=self.request.user,
            enrollments__status=Enrollment.STATUS_ACTIVE,
            is_active=True,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        course = self.object
        student = self.request.user

        taken_ids = set(
            Result.objects.filter(student=student, exam__courses=course)
            .values_list('exam_id', flat=True)
        )

        exams_info = []
        for exam in course.exams.all():
            exams_info.append({
                'exam': exam,
                'taken': exam.pk in taken_ids,
                'active': exam.is_active(),
                'upcoming': exam.is_upcoming(),
            })

        ctx['exams_info'] = exams_info
        ctx['enrollment'] = Enrollment.objects.get(student=student, course=course)
        return ctx
