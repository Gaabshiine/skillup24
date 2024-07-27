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

    path("membership/", views.membership_view, name="membership"),

    path("faqs/", views.faqs_view, name="faqs"),

    # event urls
    path("event_list/", views.event_list_view, name="event_list"),
    path("event_detail/<int:id>/", views.event_detail_view, name="event_detail"),


    path("zoom_meeting_list/", views.zoom_meeting_list_view, name="zoom_meeting_list"),
    path("zoom_meeting_detail/<int:id>/", views.zoom_meeting_detail_view, name="zoom_meeting_detail"),

    # course details
    path("course_list/", views.course_list_view, name="course_list"),
    path("course_detail/<int:id>/", views.course_detail_view, name="course_detail"),
    path("course_category/<int:id>/", views.course_category_view, name="course_category"),

    # intructors
    path("instructor_list/", views.instructor_list_view, name="instructor_list"),
    path("instructor_detail/<int:id>/", views.instructor_detail_view, name="instructor_detail"),



    path("purchase/", views.purchase_view, name="purchase"),

   
   # checkout either for purchased or empty purchase for the student
   path("checkout/", views.checkout_view, name="checkout"),


    # student dashboard or profile
    path("student_dasbhoard/<int:id>/", views.student_dashboard, name="student_dashboard"),
    path("my_profile/<int:id>/", views.student_profile, name="student_profile"),
    path("enrolled_courses/<int:id>/", views.enrolled_courses, name="enrolled_courses"),
    path("wish_list/<int:id>/", views.wish_list, name="wish_list"),
    # review 
    path("review/<int:id>/", views.review_view, name="review"),

    # quiz attempts
    path("quiz_attempts/<int:id>/", views.quiz_attempts, name="quiz_attempts"),
    path("quiz_attempt_detail/<int:id>/", views.quiz_attempt_detail, name="quiz_attempt_detail"),

    
    path("purchase_history/<int:id>/", views.purchase_history, name="purchase_history"),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    path('certificates/<int:id>/', views.certificates_view, name='certificates'),

    



    

    
   
 


    

]
