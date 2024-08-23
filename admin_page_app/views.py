from django.shortcuts import render
from django.shortcuts import render, redirect
from .utils import execute_query
from django.http import JsonResponse
from django.conf import settings
import os
from django.urls import reverse
from datetime import datetime
from django.http import Http404
from .models import Category, Course, Payment
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.http import require_POST
from home_page_app.views import generate_certificate_pdf









#--------------------------------- 1) Start: Admin Dashboard---------------------------------#
# 1.1) Admin Dashboard
def dashboard(request):
    # Revenue Over Time (Line Chart)
    revenue_query = """
        SELECT DATE_FORMAT(p.payment_date, '%Y-%m') AS month, SUM(p.total_amount) AS revenue
        FROM payments p
        WHERE p.status = 'approved'
        GROUP BY month
        ORDER BY month;
    """
    revenue_data = execute_query(revenue_query, fetchall=True)
    revenue_labels = [row['month'] for row in revenue_data]
    revenue_values = [float(row['revenue']) for row in revenue_data]

    # Enrollment by Category (Donut Chart)
    enrollment_query = """
        SELECT cat.name AS category_name, COUNT(e.id) AS enrollments
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN categories cat ON c.category_id = cat.id
        GROUP BY cat.name
        ORDER BY enrollments DESC;
    """
    enrollment_data = execute_query(enrollment_query, fetchall=True)
    category_labels = [row['category_name'] for row in enrollment_data]
    enrollment_values = [row['enrollments'] for row in enrollment_data]

    # Top 5 Courses by Enrollment (Bar Chart)
    top_courses_query = """
        SELECT c.name AS course_name, COUNT(e.id) AS enrollments
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        GROUP BY c.name
        ORDER BY enrollments DESC
        LIMIT 5;
    """
    top_courses_data = execute_query(top_courses_query, fetchall=True)
    top_courses_labels = [row['course_name'] for row in top_courses_data]
    top_courses_values = [row['enrollments'] for row in top_courses_data]

    # Card Data
    registered_students_query = "SELECT COUNT(*) AS count FROM students"
    registered_students_count = execute_query(registered_students_query, fetchone=True)['count']

    registered_instructors_query = "SELECT COUNT(*) AS count FROM instructors"
    registered_instructors_count = execute_query(registered_instructors_query, fetchone=True)['count']

    total_courses_query = "SELECT COUNT(*) AS count FROM courses"
    total_courses_count = execute_query(total_courses_query, fetchone=True)['count']

    total_categories_query = "SELECT COUNT(*) AS count FROM categories"
    total_categories_count = execute_query(total_categories_query, fetchone=True)['count']

    total_revenue_query = "SELECT SUM(total_amount) AS revenue FROM payments WHERE status = 'approved'"
    total_revenue = execute_query(total_revenue_query, fetchone=True)['revenue']

    total_enrollments_query = "SELECT COUNT(*) AS count FROM enrollments"
    total_enrollments_count = execute_query(total_enrollments_query, fetchone=True)['count']

    pending_payments_query = "SELECT COUNT(*) AS count FROM payments WHERE status = 'pending'"
    pending_payments_count = execute_query(pending_payments_query, fetchone=True)['count']

    # Pass the data to the template context
    context = {
        'revenue_labels': revenue_labels,
        'revenue_values': revenue_values,
        'category_labels': category_labels,
        'enrollment_values': enrollment_values,
        'top_courses_labels': top_courses_labels,
        'top_courses_values': top_courses_values,
        'registered_students_count': registered_students_count,
        'registered_instructors_count': registered_instructors_count,
        'total_courses_count': total_courses_count,
        'total_categories_count': total_categories_count,
        'total_revenue': total_revenue,
        'total_enrollments_count': total_enrollments_count,
        'pending_payments_count': pending_payments_count,
    }

    return render(request, 'admin_page_app/admin_dashboard.html', context)


#--------------------------------- End: Admin Dashboard---------------------------------#





#--------------------------------- 2) Start: views and details all about the system ---------------------------------#

# 2.1) View all students
def student_list(request):
    students = execute_query("SELECT * FROM students", fetchall=True)
    return render(request, 'admin_page_app/view_students.html', {'students': students}) 


# 2.2) View all instructors
def instructor_list(request):
    instructors = execute_query("SELECT * FROM instructors", fetchall=True)
    return render(request, 'admin_page_app/view_instructors.html', {'instructors': instructors}) 


# 2.3) View all admins
def view_admins(request):
    # Query to fetch all admins
    query = "SELECT * FROM admins ORDER BY created_at DESC"
    admins = execute_query(query, fetchall=True)

    # Render the admins list page
    return render(request, 'admin_page_app/view_admins.html', {'admins': admins})


# 2.4) View all categories
def category_list(request):
    categories = execute_query("SELECT * FROM categories", [], fetchall=True)  # Fetch categories from DB
    return render(request, 'admin_page_app/view_categories.html', {
        'categories': categories,
        'MEDIA_URL': settings.MEDIA_URL
    })


# 2.5) View all courses
def course_list(request):
    query = """
        SELECT c.id, c.name, c.start_date, c.end_date, c.course_amount,
               c.image, cat.name as category_name, i.first_name as instructor_first_name, i.last_name as instructor_last_name
        FROM courses c
        JOIN categories cat ON c.category_id = cat.id
        JOIN instructors i ON c.instructor_id = i.id
    """
    courses = execute_query(query, fetchall=True)
    return render(request, 'admin_page_app/view_courses.html', {'courses': courses})



# 2.6) View all payments
def payment_list(request):
    payments_query = """
        SELECT 
            p.id, p.expected_course_amount, p.discount, p.total_amount, p.payment_date,
            p.status, p.student_id, s.first_name, s.last_name
        FROM 
            payments p
        JOIN 
            students s ON p.student_id = s.id
        ORDER BY p.id DESC
    """
    payments = execute_query(payments_query, fetchall=True)

    return render(request, 'admin_page_app/view_payments.html', {
        'payments': payments,
    })



# 2.7) View all lessons
def lesson_list(request):
    # Fetch lessons with related course and category information
    lessons = execute_query("""
        SELECT l.id, l.title, l.content, l.video_url, l.course_id, c.name as course_name, cat.name as category_name
        FROM lessons l
        JOIN courses c ON l.course_id = c.id
        JOIN categories cat ON c.category_id = cat.id
    """, [], fetchall=True)

    # Render lessons list template
    return render(request, 'admin_page_app/view_lessons.html', {'lessons': lessons})



# 2.8) View all faq list
def faq_list_view(request):
    faq_list_query = "SELECT * FROM faqs ORDER BY created_at DESC"
    faqs = execute_query(faq_list_query, fetchall=True)
    
    return render(request, 'admin_page_app/view_faqs.html', {'faqs': faqs})


# 2.9) View all events
def event_list(request):
    events_query = """
        SELECT e.id, e.name, e.description, e.event_date, c.name as course_name
        FROM events e
        JOIN courses c ON e.course_id = c.id
        ORDER BY e.event_date DESC
    """
    events = execute_query(events_query, fetchall=True)
    return render(request, 'admin_page_app/view_events.html', {'events': events})


# 2.10) view all certificates
def certificate_list(request):
    certificates_query = """
        SELECT MIN(c.id) as certificate_id, MIN(c.issue_date) as issue_date, 
               s.id as student_id, 
               CONCAT(s.first_name, ' ', s.middle_name, ' ', s.last_name) as student_name
        FROM certificates c
        JOIN students s ON c.student_id = s.id
        GROUP BY s.id
        ORDER BY MIN(c.issue_date) DESC
    """
    certificates = execute_query(certificates_query, fetchall=True)
    
    return render(request, 'admin_page_app/view_certificates.html', {'certificates': certificates})



# 2.11) view all student details
def view_student_details(request, student_id):
    # Fetch student information
    student_query = """
        SELECT id, first_name, middle_name, last_name, phone_number, email_address, address
        FROM students
        WHERE id = %s
    """
    student = execute_query(student_query, [student_id], fetchone=True)

    # Fetch profile information (optional)
    profile_query = """
        SELECT bio, profile_picture, facebook, twitter, linkedIn, github
        FROM profiles
        WHERE user_id = %s AND user_type = 'student'
    """
    profile = execute_query(profile_query, [student_id], fetchone=True)
    profile_picture_url = f"/media/{profile['profile_picture']}" if profile and profile['profile_picture'] else None

    # Fetch enrolled courses
    enrolled_courses_query = """
        SELECT ec.id as enrollment_id, c.name as course_name, cat.name as category_name
        FROM enrollments ec
        JOIN courses c ON ec.course_id = c.id
        JOIN categories cat ON c.category_id = cat.id
        WHERE ec.student_id = %s
    """
    enrolled_courses = execute_query(enrolled_courses_query, [student_id], fetchall=True)

    # Fetch reviews
    reviews_query = """
        SELECT r.rating, r.review_text, c.name as course_name, r.created_at
        FROM reviews r
        JOIN courses c ON r.course_id = c.id
        WHERE r.student_id = %s
        ORDER BY r.created_at DESC
    """
    reviews = execute_query(reviews_query, [student_id], fetchall=True)

    context = {
        'student': student,
        'profile': profile,
        'profile_picture_url': profile_picture_url,
        'enrolled_courses': enrolled_courses,
        'reviews': reviews,
    }

    return render(request, 'admin_page_app/view_student_details.html', context)


def view_student_certificates(request, student_id):
    student_certificates_query = """
        SELECT c.id, c.issue_date, 
               CONCAT(s.first_name, ' ', s.middle_name, ' ', s.last_name) as student_name, 
               cr.name as course_name
        FROM certificates c
        JOIN students s ON c.student_id = s.id
        JOIN courses cr ON c.course_id = cr.id
        WHERE s.id = %s
        ORDER BY c.issue_date DESC
    """
    student_certificates = execute_query(student_certificates_query, [student_id], fetchall=True)
    
    return render(request, 'admin_page_app/view_student_certificates.html', {'certificates': student_certificates})


def view_student_payments(request, student_id):
    # Fetch all payments related to the student's courses
    payments_query = """
        SELECT 
            p.id, p.expected_course_amount, p.discount, p.total_amount, p.payment_date,
            p.status, p.sender_phone_number, c.name as course_name
        FROM 
            payments p
        JOIN 
            courses c ON p.course_id = c.id
        WHERE 
            p.student_id = %s
        ORDER BY p.payment_date DESC
    """
    payments = execute_query(payments_query, [student_id], fetchall=True)

    if not payments:
        return render(request, '404.html', {"message": "No payments found for this student."})

    student_query = """
        SELECT first_name, last_name FROM students WHERE id = %s
    """
    student = execute_query(student_query, [student_id], fetchone=True)

    return render(request, 'admin_page_app/view_student_payments.html', {
        'payments': payments,
        'student': student,
    })


def view_category_courses(request, category_id):
    # Fetch the specific category
    category = execute_query("SELECT * FROM categories WHERE id = %s", [category_id], fetchone=True)

    # Fetch courses associated with the category, including instructor's name
    courses = execute_query("""
        SELECT c.id, c.name, c.description, c.start_date, c.end_date, 
               c.course_amount, c.image, i.first_name, i.last_name
        FROM courses c
        JOIN instructors i ON c.instructor_id = i.id
        WHERE c.category_id = %s
    """, [category_id], fetchall=True)

    if not category:
        return render(request, 'admin_page_app/category_not_found.html')  # Render a template for category not found

    return render(request, 'admin_page_app/view_category_courses.html', {
        'category': category,
        'courses': courses,
        'MEDIA_URL': settings.MEDIA_URL
    })

def view_course_lessons(request, course_id):

    try:
        lessons = execute_query("""
            SELECT l.id, l.title, l.content, l.video_url, c.name as course_name, cat.name as category_name
            FROM lessons l
            JOIN courses c ON l.course_id = c.id
            JOIN categories cat ON c.category_id = cat.id
            WHERE l.course_id = %s
        """, [course_id], fetchall=True)
    except Exception as e:
        lessons = []
        print(e)

        

    return render(request, 'admin_page_app/view_course_lessons.html', {'lessons': lessons})



def view_video(request, lesson_id):
    # Fetch the lesson along with course and category details
    lesson = execute_query("""
        SELECT l.id, l.title, l.content, l.video_url, l.created_at,
               c.id as course_id, c.name as course_name, cat.name as category_name
        FROM lessons l
        JOIN courses c ON l.course_id = c.id
        JOIN categories cat ON c.category_id = cat.id
        WHERE l.id = %s
    """, [lesson_id], fetchone=True)

    if not lesson:
        raise Http404("Lesson not found")

    return render(request, 'admin_page_app/view_video.html', {'lesson': lesson, 'video_url': lesson['video_url']})

#--------------------------------- End: views and details all about the system ---------------------------------#



#--------------------------------- 3) Start: Add views record to the system ---------------------------------#

# 3.1) Add a new category
def add_categories(request):
    if request.method == 'POST':
        number_of_categories = int(request.POST.get('number_of_categories', '0'))
        errors = {}
        success = True

        for i in range(number_of_categories):
            name = request.POST.get(f'name_{i}', '').strip()
            description = request.POST.get(f'description_{i}', '').strip()
            image = request.FILES.get(f'image_{i}')
            level = request.POST.get(f'level_{i}', 'Beginner').strip()
            language = request.POST.get(f'language_{i}', 'English').strip()
            is_free = request.POST.get(f'is_free_{i}', 'false').lower() == 'true'

            # Validate inputs
            if not name:
                errors[f'name_{i}'] = 'Name is required.'
                success = False
            if not description:
                errors[f'description_{i}'] = 'Description is required.'
                success = False

            # Check if the category already exists
            query = "SELECT COUNT(*) FROM categories WHERE name = %s"
            if execute_query(query, [name], fetchone=True)['COUNT(*)'] > 0:
                errors[f'name_{i}'] = 'Category already exists.'
                success = False

            # Handle image upload
            image_path = None
            if image:
                image_directory = os.path.join(settings.MEDIA_ROOT, 'category_images')
                os.makedirs(image_directory, exist_ok=True)
                image_path = os.path.join(image_directory, image.name)

                with open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)

                image_path = f'category_images/{image.name}'

            # Insert the new category into the database
            if success:
                query = """
                    INSERT INTO categories (name, description, image, level, language, is_free, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """
                params = [name, description, image_path, level, language, is_free]
                execute_query(query, params)

        if success:
            return JsonResponse({
                'success': True,
                'message': 'Categories added successfully!',
                'redirect_url': reverse('admin_page_app:category_list')
            })
        else:
            return JsonResponse({'success': False, 'errors': errors})

    return render(request, 'admin_page_app/admin_category_register.html')


# 3.2) Add a new course
def add_courses(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        number_of_courses = int(request.POST.get('number_of_courses', 0))
        category_id = request.POST.get('category')

        errors = {}

        if number_of_courses <= 0:
            errors['number_of_courses'] = 'Number of courses must be greater than zero.'
        if not category_id:
            errors['category'] = 'Category is required.'

        courses = []
        for i in range(number_of_courses):
            name = request.POST.get(f'name_{i}', '').strip()
            description = request.POST.get(f'description_{i}', '').strip()
            start_date = request.POST.get(f'start_date_{i}', '')
            end_date = request.POST.get(f'end_date_{i}', '')
            course_amount = request.POST.get(f'course_amount_{i}', '')
            instructor_id = request.POST.get(f'instructor_{i}', '')
            image = request.FILES.get(f'image_{i}')

            if not name:
                errors[f'name_{i}'] = f'Name for course {i+1} is required.'
            if not description:
                errors[f'description_{i}'] = f'Description for course {i+1} is required.'
            if not start_date:
                errors[f'start_date_{i}'] = f'Start date for course {i+1} is required.'
            if not course_amount:
                errors[f'course_amount_{i}'] = f'Course amount for course {i+1} is required.'
            if not instructor_id:
                errors[f'instructor_{i}'] = f'Instructor for course {i+1} is required.'

            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if end_date:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                errors[f'start_date_{i}'] = f'Invalid date format for course {i+1}.'

            image_path = None
            if image:
                image_directory = os.path.join(settings.MEDIA_ROOT, 'course_images')
                os.makedirs(image_directory, exist_ok=True)
                image_path = os.path.join(image_directory, image.name)
                with open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                image_path = f'course_images/{image.name}'

            courses.append({
                'name': name,
                'description': description,
                'start_date': start_date,
                'end_date': end_date,
                'course_amount': course_amount,
                'category_id': category_id,
                'instructor_id': instructor_id,
                'image': image_path,
            })

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        for course in courses:
            query = """
                INSERT INTO courses (name, description, start_date, end_date, course_amount, category_id, instructor_id, image, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            params = [
                course['name'], course['description'], course['start_date'],
                course['end_date'], course['course_amount'], course['category_id'],
                course['instructor_id'], course['image']
            ]
            execute_query(query, params)

        return JsonResponse({'success': True, 'message': 'Courses added successfully!', 'redirect_url': reverse('admin_page_app:course_list')})

    categories = execute_query("SELECT id, name FROM categories", [], fetchall=True)
    instructors = execute_query("SELECT id, first_name, last_name FROM instructors", [], fetchall=True)
    return render(request, 'admin_page_app/admin_course_register.html', {'categories': categories, 'instructors': instructors})

# 3.3) Add a new payment
def add_payment(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        course_id = request.POST.get('course')
        expected_course_amount = request.POST.get('expected_course_amount', '0.00')
        discount = request.POST.get('discount', '0.00')
        payment_date = request.POST.get('payment_date')

        # Calculate total amount after discount
        try:
            expected_course_amount = float(expected_course_amount)
            discount = float(discount)
            total_amount = expected_course_amount - (expected_course_amount * (discount / 100))
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid amount or discount format.'})

        # Validate inputs
        errors = {}
        if not student_id:
            errors['student'] = 'Student is required.'
        if not course_id:
            errors['course'] = 'Course is required.'
        if not payment_date:
            errors['payment_date'] = 'Payment date is required.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Check if the student is enrolled in the course
        enrollment_exists = execute_query(
            "SELECT COUNT(*) as count FROM enrollments WHERE student_id = %s AND course_id = %s",
            [student_id, course_id],
            fetchone=True
        )
        if not enrollment_exists or enrollment_exists['count'] == 0:
            return JsonResponse({'success': False, 'error': 'The student is not enrolled in this course.'})

        # Insert the payment into the database
        query = """
            INSERT INTO payments (student_id, course_id, expected_course_amount, discount, total_amount, payment_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = [student_id, course_id, expected_course_amount, discount, total_amount, payment_date]
        execute_query(query, params)

        return JsonResponse({'success': True, 'redirect_url': reverse('admin_page_app:payment_list')})

    # Fetch students who are enrolled in at least one course
    students = execute_query("""
        SELECT DISTINCT students.id, students.first_name, students.last_name
        FROM students
        INNER JOIN enrollments ON students.id = enrollments.student_id
    """, [], fetchall=True)

    # Fetch available courses
    courses = execute_query("SELECT id, name FROM courses", [], fetchall=True)

    return render(request, 'admin_page_app/admin_payment_register.html', {'students': students, 'courses': courses})

# 3.4) Add a new lesson
def add_lessons(request):
    courses = execute_query("""
        SELECT c.id, c.name AS course_name, cat.name AS category_name
        FROM courses c
        JOIN categories cat ON c.category_id = cat.id
    """, [], fetchall=True)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        number_of_lessons = int(request.POST.get('number_of_lessons', 0))
        course_id = request.POST.get('course', '').strip()

        errors = {}

        if not course_id:
            errors['course'] = 'Course is required.'
        
        lessons = []
        for i in range(number_of_lessons):
            title = request.POST.get(f'title_{i}', '').strip()
            content = request.POST.get(f'content_{i}', '').strip()
            duration = request.POST.get(f'duration_{i}', '').strip()
            video_url = request.POST.get(f'video_url_{i}', '').strip()

            # Validate individual lesson inputs
            if not title:
                errors[f'title_{i}'] = f'Title for lesson {i+1} is required.'
            if not content:
                errors[f'content_{i}'] = f'Content for lesson {i+1} is required.'
            if not duration:
                errors[f'duration_{i}'] = f'Duration for lesson {i+1} is required.'
            if not video_url:
                errors[f'video_url_{i}'] = f'Video embed code for lesson {i+1} is required.'

            lessons.append({
                'title': title,
                'content': content,
                'duration': duration,
                'video_url': video_url,  # Store full embed code
                'course_id': course_id,
            })
        
        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        # Insert lessons into the database
        for lesson in lessons:
            query = """
                INSERT INTO lessons (title, content, duration, course_id, video_url, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            params = [lesson['title'], lesson['content'], lesson['duration'], lesson['course_id'], lesson['video_url']]
            execute_query(query, params)
        
        return JsonResponse({
            'success': True,
            'message': 'Lessons added successfully!',
            'redirect_url': reverse('admin_page_app:list_lessons')
        })

    return render(request, 'admin_page_app/admin_lesson_register.html', {'courses': courses})


# 3.5) add FAQ
def add_faq_view(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        video_url = request.POST.get('video_url', None)
        
        insert_faq_query = """
            INSERT INTO faqs (question, answer, video_url, created_at)
            VALUES (%s, %s, %s, %s)
        """
        params = [question, answer, video_url, timezone.now()]
        execute_query(insert_faq_query, params)
        
        return redirect('admin_page_app:faq_list')

    return render(request, 'admin_page_app/admin_faq_register.html')

# 3.6) Add a new event
def add_event(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        event_date_str = request.POST['event_date']
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        event_time_str = request.POST['event_time']
        event_time = datetime.strptime(event_time_str, '%H:%M').time()
        event_place = request.POST['event_place']
        event_status = request.POST['event_status']
        course_id = request.POST['course']

        insert_query = """
            INSERT INTO events (name, description, event_date, event_time, event_place, event_status, course_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(insert_query, [name, description, event_date, event_time, event_place, event_status, course_id, timezone.now()])

        return redirect('admin_page_app:event_list')
    else:
        courses_query = "SELECT id, name FROM courses"
        courses = execute_query(courses_query, fetchall=True)
        return render(request, 'admin_page_app/admin_event_register.html', {'courses': courses})

#--------------------------------- End: Add views record to the system ---------------------------------#



#--------------------------------- 4) Start: update views record from the system ---------------------------------#

# 4.1) Update a category
def update_category(request, category_id):
    category = execute_query("SELECT * FROM categories WHERE id = %s", [category_id], fetchone=True)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        level = request.POST.get('level', 'Beginner').strip()
        language = request.POST.get('language', 'English').strip()
        is_free = request.POST.get('is_free', 'false').lower() == 'true'

        # Validate inputs
        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not description:
            errors['description'] = 'Description is required.'

        # Return errors if any
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Handle image upload
        image_path = category['image']  # Use existing image path if not updated
        if image:
            image_directory = os.path.join(settings.MEDIA_ROOT, 'category_images')
            os.makedirs(image_directory, exist_ok=True)
            image_path = os.path.join(image_directory, image.name)
            with open(image_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            image_path = f'category_images/{image.name}'

        # Update category in the database
        update_query = """
            UPDATE categories SET name = %s, description = %s, image = %s, level = %s, language = %s, is_free = %s WHERE id = %s
        """
        execute_query(update_query, [name, description, image_path, level, language, is_free, category_id])

        return JsonResponse({'success': True, 'redirect_url': reverse('admin_page_app:category_list')})

    return render(request, 'admin_page_app/admin_category_update.html', {'category': category, 'MEDIA_URL': settings.MEDIA_URL})



# 4.2) Update a course
def update_course(request, course_id):
    course = execute_query("SELECT * FROM courses WHERE id = %s", [course_id], fetchone=True)
    if not course:
        return JsonResponse({'success': False, 'error': 'Course not found.'})

    if course['start_date']:
        course['start_date'] = course['start_date'].strftime('%Y-%m-%d')
    if course['end_date']:
        course['end_date'] = course['end_date'].strftime('%Y-%m-%d')

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        course_amount = request.POST.get('course_amount', '').strip()
        category_id = request.POST.get('category', '').strip()
        instructor_id = request.POST.get('instructor', '').strip()
        image = request.FILES.get('image')

        errors = {}
        if not name:
            errors['name'] = 'Course name is required.'
        if not description:
            errors['description'] = 'Description is required.'
        if not start_date:
            errors['start_date'] = 'Start date is required.'
        if not course_amount:
            errors['course_amount'] = 'Course amount is required.'
        if not category_id:
            errors['category'] = 'Category is required.'
        if not instructor_id:
            errors['instructor'] = 'Instructor is required.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        image_path = course['image']
        if image:
            image_directory = os.path.join(settings.MEDIA_ROOT, 'course_images')
            os.makedirs(image_directory, exist_ok=True)
            image_path = os.path.join(image_directory, image.name)
            with open(image_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            image_path = f'course_images/{image.name}'

        try:
            formatted_start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            formatted_end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format. Please use YYYY-MM-DD.'})

        update_query = """
            UPDATE courses
            SET name = %s, description = %s, start_date = %s, end_date = %s,
                course_amount = %s, category_id = %s, instructor_id = %s, image = %s
            WHERE id = %s
        """
        params = [name, description, formatted_start_date, formatted_end_date, course_amount, category_id, instructor_id, image_path, course_id]
        try:
            execute_query(update_query, params)
            return JsonResponse({'success': True, 'redirect_url': reverse('admin_page_app:course_list')})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An error occurred while updating the course. {str(e)}'})

    categories = execute_query("SELECT * FROM categories", [], fetchall=True)
    instructors = execute_query("SELECT * FROM instructors", [], fetchall=True)
    return render(request, 'admin_page_app/admin_course_update.html', {
        'course': course,
        'categories': categories,
        'instructors': instructors,
        'MEDIA_URL': settings.MEDIA_URL
    })


# # 4.3) Payment update
# def update_payment(request, payment_id):
#     payment = execute_query("SELECT * FROM payments WHERE id = %s", [payment_id], fetchone=True)
#     if not payment:
#         return JsonResponse({'success': False, 'error': 'Payment not found.'})

#     if request.method == 'POST':
#         student_id = request.POST.get('student')
#         course_id = request.POST.get('course')
#         expected_course_amount = request.POST.get('expected_course_amount', '0.00')
#         discount = request.POST.get('discount', '0.00')
#         payment_date = request.POST.get('payment_date')

#         # Calculate total amount after discount
#         try:
#             expected_course_amount = float(expected_course_amount)
#             discount = float(discount)
#             total_amount = expected_course_amount - (expected_course_amount * (discount / 100))
#         except ValueError:
#             return JsonResponse({'success': False, 'error': 'Invalid amount or discount format.'})

#         # Validate inputs
#         errors = {}
#         if not student_id:
#             errors['student'] = 'Student is required.'
#         if not course_id:
#             errors['course'] = 'Course is required.'
#         if not payment_date:
#             errors['payment_date'] = 'Payment date is required.'

#         if errors:
#             return JsonResponse({'success': False, 'errors': errors})

#         # Check if the student is enrolled in the course
#         enrollment_exists = execute_query(
#             "SELECT COUNT(*) as count FROM enrollments WHERE student_id = %s AND course_id = %s",
#             [student_id, course_id],
#             fetchone=True
#         )
#         if not enrollment_exists or enrollment_exists['count'] == 0:
#             return JsonResponse({'success': False, 'error': 'The student is not enrolled in this course.'})

#         # Update the payment in the database
#         query = """
#             UPDATE payments
#             SET student_id = %s, course_id = %s, expected_course_amount = %s, discount = %s, total_amount = %s, payment_date = %s
#             WHERE id = %s
#         """
#         params = [student_id, course_id, expected_course_amount, discount, total_amount, payment_date, payment_id]
#         execute_query(query, params)

#         return JsonResponse({'success': True, 'redirect_url': reverse('admin_page_app:payment_list')})

#     # Fetch the payment details for editing
#     students = execute_query("""
#         SELECT DISTINCT students.id, students.first_name, students.last_name
#         FROM students
#         INNER JOIN enrollments ON students.id = enrollments.student_id
#     """, [], fetchall=True)

#     courses = execute_query("SELECT id, name FROM courses", [], fetchall=True)

#     return render(request, 'admin_page_app/admin_payment_update.html', {
#         'payment': payment,
#         'students': students,
#         'courses': courses
#     })



# 4.4) Update a lesson
def update_lesson(request, lesson_id):
    # Fetch the lesson details
    lesson = execute_query("""
        SELECT l.id, l.title, l.content, l.video_url, l.duration, l.created_at,
               c.id as course_id, c.name as course_name, cat.name as category_name
        FROM lessons l
        JOIN courses c ON l.course_id = c.id
        JOIN categories cat ON c.category_id = cat.id
        WHERE l.id = %s
    """, [lesson_id], fetchone=True)

    if not lesson:
        raise Http404("Lesson not found")

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        duration = request.POST.get('duration', '').strip()
        video_url = request.POST.get('video_url', '').strip()

        # Validate inputs
        errors = {}
        if not title:
            errors['title'] = 'Title is required.'
        if not content:
            errors['content'] = 'Content is required.'
        if not duration:
            errors['duration'] = 'Duration is required.'
        if not video_url:
            errors['video_url'] = 'Video URL is required.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Update the lesson in the database
        query = """
            UPDATE lessons
            SET title = %s, content = %s, duration = %s, video_url = %s
            WHERE id = %s
        """
        params = [title, content, duration, video_url, lesson_id]
        execute_query(query, params)

        return JsonResponse({'success': True, 'redirect_url': reverse('admin_page_app:list_lessons')})

    return render(request, 'admin_page_app/admin_lesson_update.html', {'lesson': lesson})

# 4.5) Update a student status
def update_payment_status(request, payment_id, status):
    # Update payment status
    update_status_query = """
        UPDATE payments
        SET status = %s
        WHERE id = %s
    """
    execute_query(update_status_query, [status, payment_id])

    # Fetch payment details
    payment_query = """
        SELECT p.*, s.email_address, s.first_name, s.last_name, c.name as course_name
        FROM payments p
        JOIN students s ON p.student_id = s.id
        JOIN courses c ON p.course_id = c.id
        WHERE p.id = %s
    """
    payment = execute_query(payment_query, [payment_id], fetchone=True)

    if status == 'approved':
        # Send enrollment email
        subject = "Your Enrollment is Confirmed"
        message = f"Dear {payment['first_name']},\n\nCongratulations! Your payment for the course {payment['course_name']} has been approved. Enjoy your course!"
        send_mail(subject, message, 'abdisalanabdukadir@gmail.com', [payment['email_address']])

        # Check if the student is already enrolled in the course
        check_enrollment_query = """
            SELECT id FROM enrollments 
            WHERE student_id = %s AND course_id = %s
        """
        enrollment_exists = execute_query(check_enrollment_query, [payment['student_id'], payment['course_id']], fetchone=True)

        if not enrollment_exists:
            # Submit to enrollments table only if no existing enrollment
            enroll_query = """
                INSERT INTO enrollments (student_id, course_id, enrollment_date)
                VALUES (%s, %s, NOW())
            """
            execute_query(enroll_query, [payment['student_id'], payment['course_id']])

    return redirect(reverse('admin_page_app:view_payments'))


# 4.6) Update a student status
def update_payment_view(request, payment_id):
    # Fetch the payment details based on the payment_id
    payment_query = """
        SELECT * FROM payments WHERE id = %s
    """
    payment = execute_query(payment_query, [payment_id], fetchone=True)
    
    if not payment:
        return JsonResponse({'success': False, 'error': 'Payment not found.'})
    
    # Fetch the list of students and courses for the dropdowns
    students_query = "SELECT id, first_name, last_name FROM students"
    students = execute_query(students_query, fetchall=True)
    
    courses_query = "SELECT id, name FROM courses"
    courses = execute_query(courses_query, fetchall=True)

    if request.method == 'POST':
        # Get the updated values from the form
        student_id = request.POST.get('student')
        course_id = request.POST.get('course')
        discount = request.POST.get('discount')
        expected_course_amount = request.POST.get('expected_course_amount')
        
        # Calculate the total amount after discount
        try:
            expected_course_amount = float(expected_course_amount)
            discount = float(discount)
            total_amount = expected_course_amount - (expected_course_amount * (discount / 100))
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid input for amount or discount.'})
        
        # Update the payment in the database
        update_payment_query = """
            UPDATE payments
            SET student_id = %s, course_id = %s, discount = %s, total_amount = %s
            WHERE id = %s
        """
        execute_query(update_payment_query, [student_id, course_id, discount, total_amount, payment_id])
        
        return JsonResponse({'success': True, 'redirect_url': reverse('admin_page_app:view_payments')})
    
    context = {
        'payment': payment,
        'students': students,
        'courses': courses,
        'total_amount': payment['total_amount']
    }
    return render(request, 'admin_page_app/admin_payment_update.html', context)


# 4.7 update faq view 
def update_faq_view(request, faq_id):
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        video_url = request.POST.get('video_url', None)

        update_faq_query = """
            UPDATE faqs 
            SET question = %s, answer = %s, video_url = %s
            WHERE id = %s
        """
        params = [question, answer, video_url, faq_id]
        execute_query(update_faq_query, params)
        
        return redirect('admin_page_app:faq_list')
    
    faq_query = "SELECT * FROM faqs WHERE id = %s"
    faq = execute_query(faq_query, [faq_id], fetchone=True)
    
    return render(request, 'admin_page_app/admin_faq_update.html', {'faq': faq})



# 4.8) Update an event
def update_event(request, event_id):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        event_date_str = request.POST['event_date']
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        event_time_str = request.POST['event_time']
        event_time = datetime.strptime(event_time_str, '%H:%M').time()
        event_place = request.POST['event_place']
        event_status = request.POST['event_status']
        course_id = request.POST['course']

        update_query = """
            UPDATE events SET name = %s, description = %s, event_date = %s, event_time = %s, event_place = %s, event_status = %s, course_id = %s WHERE id = %s
        """
        execute_query(update_query, [name, description, event_date, event_time, event_place, event_status, course_id, event_id])

        return redirect('admin_page_app:event_list')
    else:
        event_query = "SELECT * FROM events WHERE id = %s"
        event = execute_query(event_query, [event_id], fetchone=True)

        if event:
            event['event_date'] = event['event_date'].strftime('%Y-%m-%d')
            event['event_time'] = event['event_time'].strftime('%H:%M')

        courses_query = "SELECT id, name FROM courses"
        courses = execute_query(courses_query, fetchall=True)
        
        return render(request, 'admin_page_app/admin_event_update.html', {'event': event, 'courses': courses})


# 4.9) Update certificate of completion
def update_certificate(request, certificate_id):
    if request.method == 'POST':
        issue_date_str = request.POST['issue_date']
        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        student_id = request.POST['student']
        course_id = request.POST['course']

        # Validate that the student_id and course_id exist in the related tables
        student_exists_query = "SELECT COUNT(*) FROM students WHERE id = %s"
        student_exists = execute_query(student_exists_query, [student_id], fetchone=True)['COUNT(*)']

        course_exists_query = "SELECT COUNT(*) FROM courses WHERE id = %s"
        course_exists = execute_query(course_exists_query, [course_id], fetchone=True)['COUNT(*)']

        if not student_exists or not course_exists:
            print('Invalid student or course ID.')
            return redirect('admin_page_app:update_certificate', certificate_id=certificate_id)

        try:
            update_query = """
                UPDATE certificates 
                SET issue_date = %s, student_id = %s, course_id = %s 
                WHERE id = %s
            """
            execute_query(update_query, [issue_date, student_id, course_id, certificate_id])

            # Regenerate the certificate PDF with updated data
            certificate_filename = f"certificate_{student_id}_{course_id}.pdf"
            certificate_path = os.path.join(settings.MEDIA_ROOT, certificate_filename)
            generate_certificate_pdf(certificate_path, student_id, course_id)

            return redirect('admin_page_app:view_certificates')
        except Exception as e:
            print(e)
            return redirect('admin_page_app:update_certificate', certificate_id=certificate_id)

    else:
        certificate_query = """
            SELECT c.*, s.first_name, s.middle_name, s.last_name, cr.name as course_name
            FROM certificates c
            JOIN students s ON c.student_id = s.id
            JOIN courses cr ON c.course_id = cr.id
            WHERE c.id = %s
        """
        certificate = execute_query(certificate_query, [certificate_id], fetchone=True)

        if certificate:
            certificate['issue_date'] = certificate['issue_date'].strftime('%Y-%m-%d')

        students_query = "SELECT id, first_name, middle_name, last_name FROM students"
        courses_query = "SELECT id, name FROM courses"
        students = execute_query(students_query, fetchall=True)
        courses = execute_query(courses_query, fetchall=True)

        return render(request, 'admin_page_app/admin_certificate_update.html', {
            'certificate': certificate,
            'students': students,
            'courses': courses,
        })




#--------------------------------- End: update views record from the system ---------------------------------#

#--------------------------------- 5) Start: delete views record from the system ---------------------------------#

# 5.1) Delete a category
def delete_category(request, category_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # This will delete the category and all related courses and their related records
            Category.objects.filter(id=category_id).delete()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# 5.2) Delete a course
def delete_course(request, course_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # This will delete the course and all related records thanks to on_delete=models.CASCADE
            Course.objects.filter(id=course_id).delete()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method or headers.'})

# 5.3) Delete a payment
def delete_payment(request, payment_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Delete the payment using Django's ORM
            Payment.objects.filter(id=payment_id).delete()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method or headers.'})

# 5.4) Delete a lesson
def delete_lesson(request, lesson_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Delete the lesson using raw SQL query
            query = "DELETE FROM lessons WHERE id = %s"
            execute_query(query, [lesson_id])

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method or headers.'})
    
# 5.5) Delete a faq
@require_POST
def delete_faq(request, faq_id):
    try:
        delete_query = "DELETE FROM faqs WHERE id = %s"
        execute_query(delete_query, [faq_id])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# 5.6) Delete an event
@require_POST
def delete_event(request, event_id):
    try:
        delete_query = "DELETE FROM events WHERE id = %s"
        execute_query(delete_query, [event_id])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

#--------------------------------- End: delete views record from the system ---------------------------------#
# 







#--------------------------------- 6) Start: Reports ---------------------------------#
# 6.1) Payment report
def payment_report_view(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    payments = []

    if from_date and to_date:
        payments_query = """
            SELECT p.id, p.total_amount, p.payment_date, p.status, 
                   s.first_name as student_first_name, s.last_name as student_last_name, s.phone_number,
                   c.name as course_name
            FROM payments p
            JOIN students s ON p.student_id = s.id
            JOIN courses c ON p.course_id = c.id
            WHERE p.payment_date BETWEEN %s AND %s
            ORDER BY p.payment_date DESC
        """
        payments = execute_query(payments_query, [from_date, to_date], fetchall=True)

    context = {
        'payments': payments,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'admin_page_app/admin_payment_report.html', context)


# 6.2) Enrollment report
def enrollment_report_view(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    enrollments = []

    if from_date and to_date:
        enrollments_query = """
            SELECT e.id, e.enrollment_date, s.first_name as student_first_name, s.last_name as student_last_name, 
                   c.name as course_name
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            WHERE e.enrollment_date BETWEEN %s AND %s
            ORDER BY e.enrollment_date DESC
        """
        enrollments = execute_query(enrollments_query, [from_date, to_date], fetchall=True)

    context = {
        'enrollments': enrollments,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'admin_page_app/admin_course_enrollment_report.html', context)


#--------------------------------- End: Reports ---------------------------------#

