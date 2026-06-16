# ExamPortal

A full-featured online examination system built with Django.

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo   # creates demo users, exams, courses & enrollments
python manage.py runserver
```

Open http://127.0.0.1:8000

## Demo Credentials

| Role    | Username   | Password     |
|---------|------------|--------------|
| Admin   | `admin`    | `admin123`   |
| Student | `student`  | `student123` |
| Student | `student2` | `student123` |

## Features

### Admin
- **Exams** — create / edit / delete exams with schedule, duration, pass mark, shuffle
- **Questions** — MCQ, True/False, short answer; per-question marks and explanations
- **Courses** — group exams into courses with a title, code, and description
- **Enrollment** — assign one or many students to a course in one click; drop students
- **Results** — view all student submissions with scores, filter by exam

### Student
- **Dashboard** — see active exams, enrolled courses, and recent results at a glance
- **My Courses** — browse enrolled courses and their exams
- **Take Exam** — countdown timer, AJAX auto-save, auto-submit on expiry
- **Results** — detailed per-question review with correct answers and explanations

## Project Structure

```
examportal/
├── accounts/          # Custom User model (student / admin roles), auth views
├── exams/             # Exam, Question, Result, ExamSession, Course, Enrollment
│   ├── models.py
│   ├── views.py       # All CBVs — exam CRUD, course CRUD, enrollment, taking
│   ├── forms.py       # ExamForm, QuestionForm, CourseForm, EnrollStudentsForm
│   ├── urls.py
│   ├── tests.py       # 48 tests
│   └── management/commands/seed_demo.py
├── templates/
│   ├── base.html      # Sidebar layout; role-aware nav
│   ├── accounts/      # login, register, profile
│   └── exams/         # dashboards, course pages, exam-taking UI, results
└── manage.py
```

## Running Tests

```bash
python manage.py test accounts exams
# 48 tests — models, auth, exam CRUD, course CRUD, enrollment, submission
```
