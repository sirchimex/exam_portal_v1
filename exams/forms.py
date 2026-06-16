from django import forms
from django.forms import inlineformset_factory
from .models import Exam, Question


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'start_time', 'end_time', 'duration_minutes',
                  'passing_score', 'status', 'instructions', 'max_attempts', 'shuffle_questions']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['start_time'].initial = self.instance.start_time.strftime('%Y-%m-%dT%H:%M')
            self.fields['end_time'].initial = self.instance.end_time.strftime('%Y-%m-%dT%H:%M')


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'option_a', 'option_b', 'option_c', 'option_d',
                  'correct_answer', 'explanation', 'marks', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
        }


QuestionFormSet = inlineformset_factory(
    Exam, Question,
    form=QuestionForm,
    extra=1,
    can_delete=True
)


from .models import Course, Enrollment


class CourseForm(forms.ModelForm):
    exams = forms.ModelMultipleChoiceField(
        queryset=Exam.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Attach Exams',
    )

    class Meta:
        model = Course
        fields = ['title', 'code', 'description', 'exams', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, admin_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if admin_user:
            self.fields['exams'].queryset = Exam.objects.filter(created_by=admin_user)


class EnrollStudentsForm(forms.Form):
    """Bulk-enrol one or more students into a course."""
    students = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label='Select Students',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional note…'}),
    )

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        if course:
            already_enrolled = course.enrollments.filter(
                status=Enrollment.STATUS_ACTIVE
            ).values_list('student_id', flat=True)
            self.fields['students'].queryset = User.objects.filter(
                role='student'
            ).exclude(pk__in=already_enrolled)
        else:
            self.fields['students'].queryset = User.objects.filter(role='student')
