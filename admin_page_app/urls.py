from django.urls import path
from . import views

app_name = "admin_page_app"

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # # Course management
    # path('courses/', views.course_list, name='course_list'),
    # path('courses/add/', views.add_course, name='add_course'),
    # path('courses/update/<int:id>/', views.update_course, name='update_course'),
    # path('courses/delete/<int:id>/', views.delete_course, name='delete_course'),

    # # Instructor management
    # path('instructors/', views.instructor_list, name='instructor_list'),
    # path('instructors/add/', views.add_instructor, name='add_instructor'),
    # path('instructors/update/<int:id>/', views.update_instructor, name='update_instructor'),
    # path('instructors/delete/<int:id>/', views.delete_instructor, name='delete_instructor'),

    # # Student management
    # path('students/', views.student_list, name='student_list'),
    # path('students/add/', views.add_student, name='add_student'),
    # path('students/update/<int:id>/', views.update_student, name='update_student'),
    # path('students/delete/<int:id>/', views.delete_student, name='delete_student'),

    # # Reports
    # path('reports/enrollment/', views.enrollment_report, name='enrollment_report'),
    # path('reports/completion/', views.completion_report, name='completion_report'),
    # path('reports/financial/', views.financial_report, name='financial_report'),

    # # Event management
    # path('events/', views.event_list, name='event_list'),
    # path('events/add/', views.add_event, name='add_event'),
    # path('events/update/<int:id>/', views.update_event, name='update_event'),
    # path('events/delete/<int:id>/', views.delete_event, name='delete_event'),

    # # Category management
    # path('categories/', views.category_list, name='category_list'),
    # path('categories/add/', views.add_category, name='add_category'),
    # path('categories/update/<int:id>/', views.update_category, name='update_category'),
    # path('categories/delete/<int:id>/', views.delete_category, name='delete_category'),

    # # Quiz management
    # path('quizzes/', views.quiz_list, name='quiz_list'),
    # path('quizzes/add/', views.add_quiz, name='add_quiz'),
    # path('quizzes/update/<int:id>/', views.update_quiz, name='update_quiz'),
    # path('quizzes/delete/<int:id>/', views.delete_quiz, name='delete_quiz'),

    # # Certification management
    # path('certifications/', views.certification_list, name='certification_list'),
    # path('certifications/update/<int:id>/', views.update_certification, name='update_certification'),
    # path('certifications/issue/<int:id>/', views.issue_certification, name='issue_certification'),

    # # User roles and permissions management
    # path('users/', views.user_list, name='user_list'),
    # path('users/roles/', views.user_roles, name='user_roles'),
    # path('users/permissions/', views.user_permissions, name='user_permissions'),

    # # System logs
    # path('logs/', views.system_logs, name='system_logs'),
]
