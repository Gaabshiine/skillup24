# urls.py
from django.urls import path
from . import views


from django.contrib.sitemaps.views import sitemap
from skillup24.sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
}

app_name = "home_page_app"

urlpatterns = [
    path("", views.home_view, name="home"),

    path("about/", views.about_view, name="about"),

    path("contact/", views.contact_view, name="contact"),

    # event urls
    path("event_list/", views.event_list_view, name="event_list"),
    path("event_detail/<int:id>/", views.event_detail_view, name="event_detail"),
    
    


    path("zoom_meeting_list/", views.zoom_meeting_list_view, name="zoom_meeting_list"),
    path("zoom_meeting_detail/<int:id>/", views.zoom_meeting_detail_view, name="zoom_meeting_detail"),




    # course details ---> course_detail_view, submit_review
    path('courses/', views.course_list_view, name='course_list'),  # Course listing page
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('course/<int:course_id>/submit-review/', views.submit_review, name='submit_review'),
    path('category/<int:category_id>/', views.course_category_view, name='course_category'),


    # Payment urls ---> purchase_view, submit_payment_view, payment_confirmation
    path('purchase/<int:course_id>/', views.purchase_view, name='purchase'),
    path('submit_payment/', views.submit_payment_view, name='submit_payment'),
    path('payment/confirmation/', views.payment_confirmation, name='payment_confirmation'),

    # student dashboard urls ---> student_dashboard, enrolled_courses
    path('student_dashboard/<int:student_id>/', views.student_dashboard, name='student_dashboard'),
    path('enrolled_courses/', views.dashboard_enrolled_courses, name='enrolled_courses'),
    path('complete-lesson/', views.complete_lesson, name='complete_lesson'),
    path('course/<int:course_id>/enroll/', views.enroll_in_course_for_free, name='enroll_in_course_for_free'),
    
    # certificate urls ---> certificates_view
    path('certificates/', views.certificates_view, name='certificates'),

    # edit feedback and reviews
    path('edit_feedback/<int:review_id>/', views.edit_feedback_view, name='edit_feedback'),
    path('reviews/', views.review_view, name='review'),

    path('purchase-history/', views.purchase_history, name='purchase_history'),

    path('search/', views.search_results_view, name='search_results'),

   




    

    # intructors
    path("instructor_list/", views.instructor_list_view, name="instructor_list"),
    path("instructor_detail/<int:id>/", views.instructor_detail_view, name="instructor_detail"),



    

   
    # checkout either for purchased or empty purchase for the student
    path("checkout/", views.checkout_view, name="checkout"),


    # student dashboard or profile
    path("wish_list/<int:id>/", views.wish_list, name="wish_list"),
 

    # quiz attempts
    path("quiz_attempts/<int:id>/", views.quiz_attempts, name="quiz_attempts"),
    path("quiz_attempt_detail/<int:id>/", views.quiz_attempt_detail, name="quiz_attempt_detail"),

    

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),


]
