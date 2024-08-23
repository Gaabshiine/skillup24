from django.urls import path
from . import views



app_name = "account_app"

urlpatterns = [
    
    path('login/', views.login_view, name='login'),
    path('student/login/', views.model_login_view, name='model_login'),
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('student/logout/', views.student_logout_view, name='logout'),

    # reset password
    path('reset_password/', views.reset_password_request_view, name='reset_password_request'),
    path('reset_password/<uidb64>/<token>/', views.reset_password_view, name='reset_password'),

    

    # registration urls
    path('student/register/by_admin/', views.add_student_by_admin, name='add_student_by_admin'),
    path('student/register/', views.add_student_by_user, name='add_student_by_user'),
    path('student/add/', views.add_student_from_slider, name='add_student_from_slider'),
    path('register_instructor/', views.add_instructor_by_admin, name='add_instructor'),
    path('admin/register/', views.admin_register_view, name='admin_register'),
    path('admin/add/', views.admin_register_view_without_login, name='add_admin'),  # New URL for adding admin

    


    # update urls
    path('students/update/by_user/', views.update_student_and_profile_by_user, name='update_student_and_profile_by_user'),
    path('students/update/by_admin/<int:student_id>/', views.update_student_and_profile_by_admin, name='update_student_profile'),
    path('admin/update/<int:admin_id>/', views.update_admin_profile, name='update_admin'),  # New URL for updating admin
    path('instructors/update/<int:instructor_id>/', views.update_instructor_profile, name='update_instructor_profile'),

    # delete urls
    path('students/delete/<int:id>/', views.delete_student, name='delete_student'),
    path('instructors/delete/<int:id>/', views.delete_instructor, name='delete_instructor'),
    path('admin/delete/<int:id>/', views.delete_admin, name='delete_admin'),  # New URL for deleting admin

    # upload by using AJAX
    path('upload_profile_picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('upload_cover_photo/', views.upload_cover_photo, name='upload_cover_photo'),  # New URL pattern for cover photo
    path('delete_photos/', views.delete_photos, name='delete_photos'),  # Add this line

     

    

    # admin mangamenter
    # path('admins/', views.admin_list, name='admin_list'),
    # path('admins/add/', views.add_admin, name='add_admin'),

]

