from django.shortcuts import render

# Create your views here.

def home_view(request):
    return render(request, "home_page_app/index.html")


def about_view(request):
    return render(request, "home_page_app/about.html")


def contact_view(request):
    return render(request, "home_page_app/contact.html")


def membership_view(request):
    return render(request, "home_page_app/membership_plans.html")


def faqs_view(request):
    return render(request, "home_page_app/FAQs.html")


def event_list_view(request):
    return render(request, "home_page_app/event_list.html")

def event_detail_view(request, id):
    return render(request, "home_page_app/event_detail.html", {'id': id})


def zoom_meeting_list_view(request):
    return render(request, "home_page_app/zoom_meeting_list.html")

def zoom_meeting_detail_view(request, id):
    return render(request, "home_page_app/zoom_meeting_detail.html", {'id': id})


def course_list_view(request):
    return render(request, "home_page_app/course_list.html")

def course_detail_view(request, id):
    return render(request, "home_page_app/course_detail.html", {'id': id})

def course_category_view(request, id):
    return render(request, "home_page_app/course_category.html", {'id': id})



def instructor_list_view(request):
    return render(request, "home_page_app/instructor_list.html")

def instructor_detail_view(request, id):
    return render(request, "home_page_app/intructor_details.html", {'id': id})




def purchase_view(request):
    return render(request, "home_page_app/purchase.html")


def checkout_view(request):
    return render(request, "home_page_app/checkout.html")



def student_dashboard(request, id):
    return render(request, "home_page_app/dashboard_student_dashboard.html", {'id': id})


def student_profile(request, id):
    return render(request, "home_page_app/dashboard_student_profile.html", {'id': id})


def enrolled_courses(request, id):
    return render(request, "home_page_app/dashboard_enrolled_courses.html", {'id': id})


def wish_list(request, id):
    return render(request, "home_page_app/dashboard_wish_list.html", {'id': id})


def review_view(request, id):
    return render(request, "home_page_app/dashboard_review.html", {'id': id})


def quiz_attempts(request, id):
    return render(request, "home_page_app/dashboard_quiz_attempts.html", {'id': id})

def quiz_attempt_detail(request, id):
    return render(request, "home_page_app/dashboard_quiz_attempt_detail.html", {'id': id})


def purchase_history(request, id):
    return render(request, "home_page_app/dashboard_purchase_history.html", {'id': id})


def certificates_view(request, id):
    return render(request, 'home_page_app/dashboard_certificates.html', {id: id})





