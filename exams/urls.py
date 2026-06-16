from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Admin exam management
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exams/create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('exams/<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_update'),
    path('exams/<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
    path('exams/<int:pk>/questions/', views.ExamQuestionsView.as_view(), name='exam_questions'),
    path('exams/<int:exam_pk>/questions/add/', views.QuestionCreateView.as_view(), name='question_create'),
    path('questions/<int:pk>/edit/', views.QuestionUpdateView.as_view(), name='question_update'),
    path('questions/<int:pk>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),
    path('results/', views.AdminResultsView.as_view(), name='admin_results'),

    # Admin course management
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('courses/<int:pk>/enroll/', views.EnrollStudentsView.as_view(), name='course_enroll'),
    path('courses/<int:pk>/unenroll/<int:enrollment_pk>/', views.UnenrollStudentView.as_view(), name='course_unenroll'),

    # Student courses
    path('my-courses/', views.MyCoursesView.as_view(), name='my_courses'),
    path('my-courses/<int:pk>/', views.MyCourseDetailView.as_view(), name='my_course_detail'),

    # Student exam-taking
    path('available/', views.AvailableExamsView.as_view(), name='available_exams'),
    path('exam/<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('exam/<int:pk>/start/', views.StartExamView.as_view(), name='start_exam'),
    path('exam/<int:pk>/take/', views.TakeExamView.as_view(), name='take_exam'),
    path('exam/<int:pk>/save-answer/', views.SaveAnswerView.as_view(), name='save_answer'),
    path('my-results/', views.StudentResultsView.as_view(), name='student_results'),
    path('result/<int:pk>/', views.ExamResultView.as_view(), name='exam_result'),
]
