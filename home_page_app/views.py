from django.shortcuts import render, redirect
from account_app.utils import execute_query
from django.conf import settings
import os
from django.urls import reverse
from django.http import JsonResponse
from datetime import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail







# Create your views here.

# -----------------------------------------------------> 1) Start: Home Page <-----------------------------------------------------
# 1.1) Home Page

def home_view(request):
    return render(request, 'home_page_app/index.html')


def about_view(request):
    return render(request, "home_page_app/about.html")


def contact_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if not name or not email or not message:
            return JsonResponse({'success': False})

        try:
            send_mail(
                subject=f"New Contact Form Submission from {name}",
                message=message,
                from_email=email,
                recipient_list=['gaavshiineq@gmail.com'],
                fail_silently=False,
            )
            return JsonResponse({'success': True})
        except Exception as e:
            print(f"Error sending email: {e}")
            return JsonResponse({'success': False})

    return render(request, "home_page_app/contact.html")


def membership_view(request):
    return render(request, "home_page_app/membership_plans.html")


def faqs_view(request):
    return render(request, "home_page_app/FAQs.html")


def search_results_view(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return render(request, 'home_page_app/search_results.html', {'results': []})

    # Search across categories, courses, and lessons
    search_query = f"%{query}%"
    search_results_query = """
        SELECT c.id, c.name as course_name, c.description, c.image, c.course_amount as price, 
               cat.name as category_name, 
               AVG(r.rating) as average_rating, COUNT(r.id) as rating_count
        FROM courses c
        LEFT JOIN categories cat ON c.category_id = cat.id
        LEFT JOIN reviews r ON c.id = r.course_id
        WHERE c.name LIKE %s OR cat.name LIKE %s OR EXISTS (
            SELECT 1 FROM lessons l WHERE l.course_id = c.id AND l.title LIKE %s
        )
        GROUP BY c.id
    """
    results = execute_query(search_results_query, [search_query, search_query, search_query], fetchall=True)

    # Process image URLs and ratings
    for result in results:
        result['image_url'] = f"/media/{result['image']}" if result['image'] else '/static/home_page_app/images/courses-1'
        result['average_rating'] = result['average_rating'] if result['average_rating'] else 0
        result['rating_count'] = result['rating_count'] if result['rating_count'] else 0

    return render(request, 'home_page_app/search_results.html', {'results': results, 'query': query})



# -----------------------------------------------------> 1) Start: Student Dashboard and Profile <-----------------------------------------------------

# 1.1) Student Dashboard
def student_dashboard(request, student_id):
    """
    View for the student dashboard. Retrieves student profile and passes it to the template.
    """
    # Fetch the number of enrolled courses
    enrolled_courses_query = """
        SELECT COUNT(*) as enrolled_count 
        FROM enrollments 
        WHERE student_id = %s
    """
    enrolled_courses = execute_query(enrolled_courses_query, [student_id], fetchone=True)['enrolled_count']

    # Fetch the number of active courses (for example, based on whether the course end date is in the future)
    active_courses_query = """
        SELECT COUNT(*) as active_count 
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = %s AND c.end_date >= CURDATE()
    """
    active_courses = execute_query(active_courses_query, [student_id], fetchone=True)['active_count']
    try:
    # Fetch the number of completed courses (for example, based on lesson completion)
        completed_courses_query = """
            SELECT COUNT(DISTINCT e.course_id) as completed_count
            FROM enrollments e
            JOIN lessons l ON e.course_id = l.course_id
            LEFT JOIN lesson_completions lc ON lc.lesson_id = l.id AND lc.student_id = e.student_id
            WHERE e.student_id = %s
            GROUP BY e.course_id
            HAVING COUNT(l.id) = COUNT(lc.id)
        """

        completed_courses = execute_query(completed_courses_query, [student_id], fetchone=True)['completed_count']
    except Exception as e:
        print("Error: ", e)
        completed_courses = 0
        
    


        
    # Fetch the total number of students (you might want to define what "students" means in your system)
    total_students_query = """
        SELECT COUNT(*) as student_count 
        FROM students
    """
    total_students = execute_query(total_students_query, fetchone=True)['student_count']

    # Fetch the total number of courses
    total_courses_query = """
        SELECT COUNT(*) as course_count 
        FROM courses
    """
    total_courses = execute_query(total_courses_query, fetchone=True)['course_count']

    # Fetch the total earnings (for example, based on payments)
    total_earnings_query = """
        SELECT SUM(total_amount) as total_earnings 
        FROM payments 
        WHERE student_id = %s AND status = 'approved'
    """
    total_earnings = execute_query(total_earnings_query, [student_id], fetchone=True)['total_earnings']

    context = {
        'enrolled_courses': enrolled_courses,
        'active_courses': active_courses,
        'completed_courses': completed_courses,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_earnings': total_earnings,
    }

    return render(request, 'home_page_app/dashboard.html', context)

# -----------------------------------------------------> End: Student Dashboard and Profile <-----------------------------------------------------


# -----------------------------------------------------> 2) Start: Intructor Dashboard <-----------------------------------------------------
# def instructor_dashboard(request):
#     """
#     View for the instructor dashboard. Retrieves instructor profile and passes it to the template.
#     """
#     instructor_profile = None

#     # Check if the instructor_id is set in the session
#     if 'instructor_id' in request.session:
#         # Fetch instructor profile from the database
#         query = "SELECT * FROM instructors WHERE id = %s"
#         instructor_profile = execute_query(query, [request.session['instructor_id']], fetchone=True)

#     if not instructor_profile:
#         # If no instructor is found, redirect to the login page
#         return redirect(reverse('account_app:instructor_login'))

#     # Fetch or create the instructor's profile
#     profile_query = "SELECT * FROM profiles WHERE user_id = %s AND user_type = 'instructor'"
#     profile = execute_query(profile_query, [instructor_profile['id']], fetchone=True)

#     # Construct the profile picture URL
#     profile_picture_url = os.path.join(settings.MEDIA_URL, profile['profile_picture']).replace('\\', '/') if profile and profile.get('profile_picture') else None

#     # Add context for the instructor profile
#     context = {
#         'instructor_user': instructor_profile,
#         'profile_picture_url': profile_picture_url,
#     }

#     return render(request, 'instructor_page_app/instructor_dashboard.html', context)

# -----------------------------------------------------> End: Intructor Dashboard <-----------------------------------------------------






# -----------------------------------------------------> 3) Start: Course, review and payment Details <-----------------------------------------------------
def course_list_view(request):
    student_id = request.session.get('student_id')

    # Base query to fetch courses with necessary details
    query = """
        SELECT 
            c.id, c.name, c.description, c.image, c.course_amount as price, 
            cat.level, cat.is_free, cat.name as category_name, 
            AVG(r.rating) as average_rating, COUNT(r.id) as rating_count, 
            (SELECT COUNT(l.id) FROM lessons l WHERE l.course_id = c.id) as lessons_count,
            (SELECT SUM(l.duration) FROM lessons l WHERE l.course_id = c.id) as duration
        FROM 
            courses c
        JOIN 
            categories cat ON c.category_id = cat.id
        LEFT JOIN 
            reviews r ON c.id = r.course_id
    """

    # Adjust the query if the student is logged in
    if student_id:
        # Query to check if the student is enrolled in any courses
        enrollment_check_query = """
            SELECT COUNT(*) as enrolled_count
            FROM enrollments
            WHERE student_id = %s
        """
        enrolled_count = execute_query(enrollment_check_query, [student_id], fetchone=True)['enrolled_count']

        if enrolled_count > 0:
            # If the student is enrolled in courses, show only those courses
            query += """
                JOIN enrollments e ON c.id = e.course_id
                WHERE e.student_id = %s
            """
            params = [student_id]
        else:
            # If the student is not enrolled in any courses, show all courses
            params = []
    else:
        params = []
    
    query += " GROUP BY c.id, cat.name ORDER BY c.name ASC"
    
    # Execute the query with the appropriate parameters
    courses = execute_query(query, params, fetchall=True)

    # Adjust the image URL for each course
    for course in courses:
        course['image_url'] = f"/media/{course['image']}" if course['image'] else '/static/home_page_app/images/courses/courses-1.jpg'

    # Pagination setup
    paginator = Paginator(courses, 8)  # Show 8 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Render the course list template with the paginated courses
    return render(request, 'home_page_app/course_list.html', {'page_obj': page_obj})


# 3.1) Course Details
def course_detail_view(request, course_id):
    student_id = request.session.get('student_id')

    # Fetch the course details
    course_query = """
        SELECT 
            c.id, c.name, c.description, c.start_date, c.end_date, c.image,
            c.course_amount, c.category_id, c.instructor_id, cat.name as category_name,
            cat.level, cat.language, cat.is_free as category_is_free, 
            ins.first_name, ins.middle_name, ins.last_name,
            prof.profile_picture as instructor_profile
        FROM 
            courses c
        JOIN 
            categories cat ON c.category_id = cat.id
        JOIN 
            instructors ins ON c.instructor_id = ins.id
        LEFT JOIN 
            profiles prof ON ins.id = prof.user_id AND prof.user_type = 'instructor'
        WHERE 
            c.id = %s
    """
    course = execute_query(course_query, [course_id], fetchone=True)

    if not course:
        return render(request, '404.html')

    if student_id:
        # Check if the student is enrolled in the course
        check_enrollment_query = """
            SELECT e.id, p.status as payment_status
            FROM enrollments e
            LEFT JOIN payments p ON e.course_id = p.course_id AND e.student_id = p.student_id
            WHERE e.student_id = %s AND e.course_id = %s
        """
        enrollment = execute_query(check_enrollment_query, [student_id, course_id], fetchone=True)
        if enrollment:
            has_access = enrollment['payment_status'] == 'approved'
            is_enrolled = True
        else:
            has_access = False
            is_enrolled = False
    else:
        has_access = False  # No access if not logged in
        is_enrolled = False  # Not enrolled if not logged in

    # Query to fetch lessons for the course
    lessons_query = """
        SELECT id, title, video_url, duration 
        FROM lessons 
        WHERE course_id = %s 
        ORDER BY id ASC
    """
    lessons = execute_query(lessons_query, [course_id], fetchall=True)

    # Remove the 'autoplay=true' parameter from video URLs
    for lesson in lessons:
        if lesson['video_url']:
            lesson['video_url'] = lesson['video_url'].replace('autoplay=true', 'autoplay=false')

    # Calculate the total duration of all lessons
    total_duration = sum(float(lesson['duration']) for lesson in lessons)

    # Add conditional icons and video URLs to the lessons
    for lesson in lessons:
        if has_access and lesson['video_url']:
            lesson['icon'] = 'fas fa-play-circle'  # Media icon 
            lesson['media_available'] = True
        else:
            lesson['icon'] = 'fas fa-lock'  # Locked icon
            lesson['media_available'] = False

    # Fetch reviews related to the course
    reviews_query = """
        SELECT r.review_text, r.rating, s.first_name, s.last_name, r.created_at
        FROM reviews r
        JOIN students s ON r.student_id = s.id
        WHERE r.course_id = %s
    """
    reviews = execute_query(reviews_query, [course_id], fetchall=True)

    # Calculate average rating for this course
    ratings_count = len(reviews)
    if ratings_count > 0:
        average_rating = sum(review['rating'] for review in reviews) / ratings_count
        normalized_rating = average_rating / 20  # Assuming the rating is out of 100
    else:
        average_rating = 0
        normalized_rating = 0

    rating_display = "{:.1f}".format(round(normalized_rating, 1)) if normalized_rating else "No ratings"

    # Fetch related courses
    related_courses_query = """
        SELECT c.id, c.name, c.image, c.course_amount 
        FROM courses c 
        WHERE c.category_id = %s AND c.id != %s
    """
    related_courses = execute_query(related_courses_query, [course['category_id'], course_id], fetchall=True)

    # Fetch instructor's other courses count
    instructor_courses_query = """
        SELECT COUNT(*) as instructor_courses_count 
        FROM courses 
        WHERE instructor_id = %s
    """
    instructor_courses = execute_query(instructor_courses_query, [course['instructor_id']], fetchone=True)

    # Calculate the progress of the course
    progress = 0
    completed_lessons = 0
    if student_id:
        progress_query = """
            SELECT COUNT(lc.id) as completed_lessons, COUNT(l.id) as total_lessons
            FROM lessons l
            LEFT JOIN lesson_completions lc ON lc.lesson_id = l.id AND lc.student_id = %s
            WHERE l.course_id = %s
            GROUP BY l.course_id
        """
        progress_data = execute_query(progress_query, [student_id, course_id], fetchone=True)

        completed_lessons = progress_data['completed_lessons'] if progress_data else 0
        total_lessons = progress_data['total_lessons'] if progress_data else 0
        progress = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0

    # Check if a certificate has been generated
    certificate_url = None
    if student_id:
        certificate_query = """
            SELECT id FROM certificates WHERE student_id = %s AND course_id = %s
        """
        certificate = execute_query(certificate_query, [student_id, course_id], fetchone=True)

        if certificate:
            certificate_url = f"/media/certificate_{student_id}_{course_id}.pdf"

    # Prepare the context for the template
    context = {
        'course': course,
        'course_image_url': f"/media/{course['image']}" if course.get('image') else None,
        'instructor_profile': f"/media/{course.get('instructor_profile')}" if course.get('instructor_profile') else None,
        'lessons': lessons,
        'total_duration': total_duration,
        'reviews': reviews,
        'average_rating': average_rating,
        'rating_display': rating_display,
        'ratings_count': ratings_count,
        'related_courses': related_courses,
        'instructor_courses': instructor_courses['instructor_courses_count'] if instructor_courses else 0,
        'rating_range': [i * 20 for i in range(1, 6)],
        'first_video': lessons[0]['video_url'] if lessons else None,
        'has_access': has_access,
        'is_enrolled': is_enrolled,
        'progress': progress,
        'completed_lessons': completed_lessons,
        'certificate_url': certificate_url,
    }

    return render(request, 'home_page_app/student_course_details.html', context)



# 3.1.1) Course completion
@csrf_exempt
def complete_lesson(request):
    if request.method == "POST":
        student_id = request.session.get('student_id')
        lesson_id = request.POST.get('lesson_id')
        course_id = request.POST.get('course_id')

        if not student_id or not lesson_id or not course_id:
            return JsonResponse({'success': False, 'message': 'Invalid data provided.'}, status=400)

        # Check if the lesson is already marked as completed
        already_completed_query = """
            SELECT 1 FROM lesson_completions 
            WHERE student_id = %s AND lesson_id = %s
        """
        already_completed = execute_query(already_completed_query, [student_id, lesson_id], fetchone=True)

        if already_completed:
            return JsonResponse({'success': False, 'message': 'Lesson already completed.'}, status=400)

        # Insert the completion record
        insert_completion_query = """
            INSERT INTO lesson_completions (student_id, course_id, lesson_id, completion_date)
            VALUES (%s, %s, %s, NOW())
        """
        execute_query(insert_completion_query, [student_id, course_id, lesson_id])

        # Calculate the progress
        total_lessons_query = """
            SELECT COUNT(*) as total_lessons FROM lessons WHERE course_id = %s
        """
        total_lessons = execute_query(total_lessons_query, [course_id], fetchone=True)['total_lessons']

        completed_lessons_query = """
            SELECT COUNT(*) as completed_lessons FROM lesson_completions 
            WHERE student_id = %s AND course_id = %s
        """
        completed_lessons = execute_query(completed_lessons_query, [student_id, course_id], fetchone=True)['completed_lessons']

        progress = (completed_lessons / total_lessons) * 100

        # Check if all lessons are completed, and generate a certificate if necessary
        certificate_url = None
        if completed_lessons == total_lessons:
            # Generate a certificate
            certificate_query = """
                SELECT id FROM certificates WHERE student_id = %s AND course_id = %s
            """
            certificate = execute_query(certificate_query, [student_id, course_id], fetchone=True)

            if not certificate:
                # Insert the certificate record
                insert_certificate_query = """
                    INSERT INTO certificates (issue_date, student_id, course_id, created_at)
                    VALUES (NOW(), %s, %s, NOW())
                """
                execute_query(insert_certificate_query, [student_id, course_id])

                # Generate the PDF certificate
                certificate_filename = f"certificate_{student_id}_{course_id}.pdf"
                certificate_path = os.path.join(settings.MEDIA_ROOT, certificate_filename)
                generate_certificate_pdf(certificate_path, student_id, course_id)
                certificate_url = f"/media/{certificate_filename}"

        return JsonResponse({'success': True, 'progress': progress, 'completed_lessons': completed_lessons, 'certificate_url': certificate_url})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


# 3.1.2) Certificate Generation
def generate_certificate_pdf(filepath, student_id, course_id):
    student_query = """
        SELECT first_name, middle_name, last_name FROM students WHERE id = %s
    """
    student = execute_query(student_query, [student_id], fetchone=True)

    course_query = """
        SELECT name FROM courses WHERE id = %s
    """
    course = execute_query(course_query, [course_id], fetchone=True)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Add the logo
    logo_path = os.path.join(settings.STATIC_ROOT, "home_page_app/images/logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 40, height - 100, width=150, preserveAspectRatio=True, mask='auto')

    # Certificate Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height - 150, "Certificate of Completion")

    # Student's Name
    c.setFont("Helvetica", 18)
    student_name = f"{student['first_name']} {student['middle_name']} {student['last_name']}"
    c.drawCentredString(width / 2.0, height - 200, f"This is to certify that {student_name}")

    # Course Name
    course_name = course['name']
    c.drawCentredString(width / 2.0, height - 250, f"has successfully completed the course '{course_name}'")

    # Company Name
    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(width / 2.0, height - 350, "Skillup 24")

    # Date of Issue
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2.0, height - 450, f"Issue Date: {datetime.now().strftime('%Y-%m-%d')}")

    c.showPage()
    c.save()

    if not os.path.exists(filepath):
        raise ValueError(f"Certificate PDF not saved at {filepath}")


# 3.1.3) Enroll in a course
def dashboard_enrolled_courses(request):
    student_id = request.session.get('student_id')

    # Fetch enrolled courses for the student along with the status from the payments table
    enrolled_courses_query = """
        SELECT c.id as course_id, c.name as course_name, c.image as course_image, 
               cat.name as category_name, p.status as payment_status
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN categories cat ON c.category_id = cat.id
        JOIN payments p ON p.course_id = c.id AND p.student_id = e.student_id
        WHERE e.student_id = %s
    """
    enrolled_courses = execute_query(enrolled_courses_query, [student_id], fetchall=True)

    # Fetch lesson completions for the student to calculate progress
    progress_query = """
        SELECT l.course_id, COUNT(lc.id) as completed_lessons, COUNT(l.id) as total_lessons
        FROM lessons l
        LEFT JOIN lesson_completions lc ON lc.lesson_id = l.id AND lc.student_id = %s
        GROUP BY l.course_id
    """
    course_progress = execute_query(progress_query, [student_id], fetchall=True)
    
    # Prepare progress data for easier access in the template
    progress_data = {item['course_id']: item for item in course_progress}

    for course in enrolled_courses:
        course_id = course['course_id']
        if course_id in progress_data:
            course['completed_lessons'] = progress_data[course_id]['completed_lessons']
            course['total_lessons'] = progress_data[course_id]['total_lessons']
            course['progress'] = (course['completed_lessons'] / course['total_lessons']) * 100
        else:
            course['completed_lessons'] = 0
            course['total_lessons'] = 0
            course['progress'] = 0
        
        # Check the status of the payment and determine the course status
        if course['payment_status'] == 'approved':
            course['status'] = 'approved'
        elif course['payment_status'] == 'pending':
            course['status'] = 'pending'
        else:
            course['status'] = 'rejected'

        # Construct the full media URL for the course image
        if course['course_image']:
            course['course_image_url'] = f'/media/{course["course_image"]}'
        else:
            course['course_image_url'] = '/static/home_page_app/images/courses-1.jpg'  # Fallback image

    context = {
        'all_courses': enrolled_courses,
        'active_courses': [course for course in enrolled_courses if course['status'] == 'approved'],
        'completed_courses': [course for course in enrolled_courses if course['progress'] == 100],
    }
    return render(request, 'home_page_app/student_enrolled_courses.html', context)



# 3.2) Review Submission
def submit_review(request, course_id):
    if request.method == 'POST':
        # Fetch the logged-in student's ID from the session
        student_id = request.session.get('student_id')

        if not student_id:
            return redirect(reverse('home_page_app:login'))  # Redirect to login if not logged in

        # Retrieve the form data
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text', '').strip()

        # Validate the form data
        if not rating or not review_text:
            return redirect(reverse('home_page_app:course_detail', args=[course_id]))  # Redirect to course details with an error

        try:
            rating = int(rating)
        except ValueError:
            return redirect(reverse('home_page_app:course_detail', args=[course_id]))  # Redirect to course details with an error

        # Prepare the query to insert the review
        insert_review_query = """
            INSERT INTO reviews (review_text, rating, student_id, course_id, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = [review_text, rating, student_id, course_id, datetime.now()]

        try:
            execute_query(insert_review_query, params)
            return redirect(reverse('home_page_app:student_dashboard', args=[student_id]))  # Redirect to the student's dashboard
        except Exception as e:
            return redirect(reverse('home_page_app:course_detail', args=[course_id]))  # Redirect to course details with an error
    
    return redirect(reverse('home_page_app:course_detail', args=[course_id]))  # Redirect to course details if not a POST request


# 3.3) Payment Submission
def submit_payment_view(request):
    if request.method == 'POST':
        student_id = request.session.get('student_id')
        if not student_id:
            return redirect('account_app:login')

        course_id = request.POST.get('course_id')
        sender_phone_number = request.POST.get('sender_phone_number')
        course_amount = request.POST.get('course_amount')

        # Fetch the course details
        course_query = "SELECT * FROM courses WHERE id = %s"
        course = execute_query(course_query, [course_id], fetchone=True)

        if not course:
            return redirect('home_page_app:home')

        # Insert the payment record
        insert_payment_query = """
            INSERT INTO payments (expected_course_amount, total_amount, payment_date, sender_phone_number, status, student_id, course_id)
            VALUES (%s, %s, %s, %s, 'pending', %s, %s)
        """
        payment_params = [
            course_amount,
            course_amount,
            timezone.now().date(),
            sender_phone_number,
            student_id,
            course_id
        ]
        execute_query(insert_payment_query, payment_params)

        # Check if the student is already enrolled in the course
        check_enrollment_query = """
            SELECT id FROM enrollments 
            WHERE student_id = %s AND course_id = %s
        """
        enrollment_exists = execute_query(check_enrollment_query, [student_id, course_id], fetchone=True)

        if not enrollment_exists:
            # Register the student in the enrollments table only if not already enrolled
            insert_enrollment_query = """
                INSERT INTO enrollments (enrollment_date, student_id, course_id, created_at)
                VALUES (%s, %s, %s, %s)
            """
            enrollment_params = [
                timezone.now().date(),
                student_id,
                course_id,
                timezone.now()
            ]
            execute_query(insert_enrollment_query, enrollment_params)

        return redirect('home_page_app:payment_confirmation')

    return redirect('home_page_app:course_detail', course_id=course_id)



# 3.4) purchase visit view
def purchase_view(request, course_id):
    # Fetch course details
    course_query = """
        SELECT 
            c.id, c.name, c.course_amount, ins.first_name, ins.last_name 
        FROM 
            courses c 
        JOIN 
            instructors ins ON c.instructor_id = ins.id 
        WHERE 
            c.id = %s
    """
    course = execute_query(course_query, [course_id], fetchone=True)

    if not course:
        return render(request, '404.html')

    # Check if the user is logged in as a student
    student_user = request.session.get('student_id')

    context = {
        'course': course,
        'student_user': student_user,
    }
    return render(request, 'home_page_app/student_purchase.html', context)



def payment_confirmation(request):
    return render(request, 'home_page_app/student_payment_confirmation.html')


def enroll_in_course_for_free(request, course_id):
    student_id = request.session.get('student_id')
    
    if not student_id:
        # If the user is not logged in, redirect them to the login page
        return redirect('account_app:login')

    # Check if the student is already enrolled in the course
    check_enrollment_query = """
        SELECT id FROM enrollments 
        WHERE student_id = %s AND course_id = %s
    """
    enrollment_exists = execute_query(check_enrollment_query, [student_id, course_id], fetchone=True)

    if not enrollment_exists:
        # Register the student in the enrollments table
        insert_enrollment_query = """
            INSERT INTO enrollments (enrollment_date, student_id, course_id, created_at)
            VALUES (%s, %s, %s, %s)
        """
        enrollment_params = [
            timezone.now().date(),
            student_id,
            course_id,
            timezone.now()
        ]
        execute_query(insert_enrollment_query, enrollment_params)
        
        # Insert the payment record with status as 'approved'
        insert_payment_query = """
            INSERT INTO payments (expected_course_amount, total_amount, payment_date, status, student_id, course_id)
            VALUES (0, 0, %s, 'approved', %s, %s)
        """
        payment_params = [
            timezone.now().date(),
            student_id,
            course_id
        ]
        execute_query(insert_payment_query, payment_params)

    # Redirect the user back to the course detail page with access granted
    return redirect('home_page_app:course_detail', course_id=course_id)


def review_view(request):
    student_id = request.session.get('student_id')
    # admin_page_app:login
    if not student_id:
        return redirect('account_app:login')
    return render(request, "home_page_app/dashboard_review.html")



def edit_feedback_view(request, review_id):
    # Fetch the review details using the review_id
    review_query = """
        SELECT r.id, r.review_text, r.rating, c.name as course_name, r.created_at
        FROM reviews r
        JOIN courses c ON r.course_id = c.id
        WHERE r.id = %s
    """
    review = execute_query(review_query, [review_id], fetchone=True)

    if not review:
        raise Http404("Review not found")

    if request.method == 'POST':
        review_text = request.POST.get('review_text')
        rating = request.POST.get('rating')

        # Update the review in the database
        update_review_query = """
            UPDATE reviews
            SET review_text = %s, rating = %s
            WHERE id = %s
        """
        execute_query(update_review_query, [review_text, rating, review_id])

        return JsonResponse({'success': True})  # Send a success response

    context = {
        'review': review,
    }
    return render(request, 'home_page_app/dashboard_review_update.html', context)


def purchase_history(request):
    student_id = request.session.get('student_id')

    # Fetch the purchase history for the student
    purchases_query = """
        SELECT p.id, p.total_amount, p.status, p.payment_date, 
               c.name as course_name, c.image as course_image
        FROM payments p
        JOIN courses c ON p.course_id = c.id
        WHERE p.student_id = %s
    """
    purchases = execute_query(purchases_query, [student_id], fetchall=True)

    # Add full image URL to each purchase
    for purchase in purchases:
        if purchase['course_image']:
            purchase['course_image_url'] = f'/media/{purchase["course_image"]}'
        else:
            purchase['course_image_url'] = '/static/home_page_app/images/courses/courses-8.jpg'  # Fallback image

    context = {
        'purchases': purchases,
    }

    return render(request, 'home_page_app/dashboard_purchase_history.html', context)


def certificates_view(request):

    student_id = request.session.get('student_id')
    # admin_page_app:login
    if not student_id:
        return redirect('account_app:login')
    return render(request, 'home_page_app/dashboard_certificates.html')
# -----------------------------------------------------> End: Course, review and payment Details <-----------------------------------------------------



# -----------------------------------------------------> 4) Start: Events <-----------------------------------------------------


def event_list_view(request):
    student_id = request.session.get('student_id')
    
    if student_id:
        # If the student is logged in, fetch only events related to the courses they've enrolled in
        events_query = """
            SELECT e.id, e.name, e.description, e.event_date, e.event_time, e.event_place, e.event_status, c.image as course_image
            FROM events e
            INNER JOIN courses c ON e.course_id = c.id
            INNER JOIN enrollments en ON en.course_id = c.id
            WHERE en.student_id = %s
            ORDER BY e.event_date DESC
        """
        events = execute_query(events_query, params=[student_id], fetchall=True)
        hide_amount = True
    else:
        # Otherwise, fetch all events
        events_query = """
            SELECT e.id, e.name, e.description, e.event_date, e.event_time, e.event_place, e.event_status, c.course_amount, c.image as course_image
            FROM events e
            INNER JOIN courses c ON e.course_id = c.id
            ORDER BY e.event_date DESC
        """
        events = execute_query(events_query, fetchall=True)
        hide_amount = False
    
    context = {
        'events': events,
        'hide_amount': hide_amount,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'home_page_app/event_list.html', context)

def event_detail_view(request, id):
    student_id = request.session.get('student_id')
    
    if student_id:
        # Check if the student is enrolled in the course
        enrollment_query = """
            SELECT COUNT(*)
            FROM enrollments en
            INNER JOIN events e ON e.course_id = en.course_id
            WHERE en.student_id = %s AND e.id = %s
        """
        is_enrolled = execute_query(enrollment_query, params=[student_id, id], fetchone=True)['COUNT(*)'] > 0
    else:
        is_enrolled = False

    event_query = """
        SELECT e.id, e.name, e.description, e.event_date, e.event_time, e.event_place, e.event_status, c.course_amount, c.image as course_image
        FROM events e
        INNER JOIN courses c ON e.course_id = c.id
        WHERE e.id = %s
    """
    event = execute_query(event_query, params=[id], fetchone=True)
    
    if event:
        event['course_image'] = settings.MEDIA_URL + event['course_image']  # Ensure full URL
    
    context = {
        'event': event,
        'is_enrolled': is_enrolled,
    }
    return render(request, 'home_page_app/event_details.html', context)


def zoom_meeting_list_view(request):
    return render(request, "home_page_app/zoom_meeting_list.html")

def zoom_meeting_detail_view(request, id):
    return render(request, "home_page_app/zoom_meeting_detail.html", {'id': id})




def course_category_view(request, category_id):
    student_id = request.session.get('student_id')

    if student_id:
        # Query for courses in this category associated with the student
        courses_query = """
        SELECT c.id, c.name, c.description, c.course_amount, c.image, c.start_date, c.end_date, 
               ins.first_name as instructor_first_name, ins.last_name as instructor_last_name,
               cat.name as category_name, cat.is_free as category_is_free
        FROM courses c
        JOIN categories cat ON c.category_id = cat.id
        JOIN instructors ins ON c.instructor_id = ins.id
        JOIN enrollments e ON c.id = e.course_id
        WHERE c.category_id = %s AND e.student_id = %s
        """
        courses = execute_query(courses_query, [category_id, student_id], fetchall=True)
    else:
        # Query for all courses in this category
        courses_query = """
        SELECT c.id, c.name, c.description, c.course_amount, c.image, c.start_date, c.end_date, 
               ins.first_name as instructor_first_name, ins.last_name as instructor_last_name,
               cat.name as category_name, cat.is_free as category_is_free
        FROM courses c
        JOIN categories cat ON c.category_id = cat.id
        JOIN instructors ins ON c.instructor_id = ins.id
        WHERE c.category_id = %s
        """
        courses = execute_query(courses_query, [category_id], fetchall=True)
    
    # Process each course for display
    for course in courses:
        # Handle images
        if course['image']:
            course['image_url'] = os.path.join(settings.MEDIA_URL, course['image']).replace('\\', '/')
        else:
            course['image_url'] = os.path.join(settings.STATIC_URL, 'home_page_app/images/courses-1.jpg')
        
        # Calculate ratings for each course
        rating_query = """
        SELECT AVG(r.rating) as average_rating, COUNT(r.rating) as rating_count
        FROM reviews r
        WHERE r.course_id = %s
        """
        rating_data = execute_query(rating_query, [course['id']], fetchone=True)
        
        if rating_data and rating_data['average_rating']:
            course['rating_display'] = "{:.1f}".format(rating_data['average_rating'])
            course['rating_width'] = (rating_data['average_rating'] / 5) * 100
        else:
            course['rating_display'] = "0.0"
            course['rating_width'] = 0

        course['rating_count'] = rating_data['rating_count'] if rating_data else 0

    context = {
        'courses': courses,
    }

    return render(request, 'home_page_app/course_category.html', context)


def instructor_list_view(request):
    return render(request, "home_page_app/instructor_list.html")

def instructor_detail_view(request, id):
    return render(request, "home_page_app/intructor_details.html", {'id': id})



def checkout_view(request):
    return render(request, "home_page_app/checkout.html")


def wish_list(request, id):
    return render(request, "home_page_app/dashboard_wish_list.html", {'id': id})


def quiz_attempts(request, id):
    return render(request, "home_page_app/dashboard_quiz_attempts.html", {'id': id})

def quiz_attempt_detail(request, id):
    return render(request, "home_page_app/dashboard_quiz_attempt_detail.html", {'id': id})
