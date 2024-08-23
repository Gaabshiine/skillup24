from admin_page_app.utils import execute_query
from django.conf import settings
import os
from datetime import datetime
from django.utils.timesince import timesince



def course_context_processor(request):
    student_id = request.session.get('student_id')

    # Base query to fetch all courses with necessary details
    all_courses_query = """
        SELECT 
            c.id, c.name, c.description, c.course_amount, c.image, c.start_date, c.end_date, 
            cat.name as category_name, cat.is_free as category_is_free,
            ins.first_name as instructor_first_name, ins.last_name as instructor_last_name,
            EXISTS(
                SELECT 1 
                FROM enrollments e 
                WHERE e.course_id = c.id AND e.student_id = %s
            ) AS is_enrolled
        FROM 
            courses c
        JOIN 
            categories cat ON c.category_id = cat.id
        JOIN 
            instructors ins ON c.instructor_id = ins.id
    """
    
    # Execute the query with the student's ID as a parameter
    all_courses = execute_query(all_courses_query, [student_id], fetchall=True)

    # Calculate average ratings for each course
    for course in all_courses:
        # Process images
        if course['image']:
            course['image_url'] = os.path.join(settings.MEDIA_URL, course['image']).replace('\\', '/')
        else:
            course['image_url'] = os.path.join(settings.STATIC_URL, 'home_page_app/images/courses-1.jpg')

        # Query to fetch average rating for each course
        rating_query = """
        SELECT AVG(r.rating) as average_rating, COUNT(r.rating) as rating_count
        FROM reviews r
        WHERE r.course_id = %s
        """
        rating_data = execute_query(rating_query, [course['id']], fetchone=True)
        
        if rating_data and rating_data['average_rating']:
            # Calculate the average rating on a scale of 1 to 5
            average_rating = rating_data['average_rating']
            course['rating_display'] = "{:.1f}".format(average_rating)
            course['rating_width'] = (average_rating / 5) * 100
        else:
            course['rating_display'] = "0.0"
            course['rating_width'] = 0

        course['rating_count'] = rating_data['rating_count'] if rating_data else 0

    # Separate free and premium courses
    free_courses = [course for course in all_courses if course['category_is_free'] == 1]
    premium_courses = [course for course in all_courses if course['category_is_free'] == 0]

    # Count all courses
    all_courses_count = len(all_courses)
    
    return {
        'all_courses': all_courses,
        'free_courses': free_courses,
        'premium_courses': premium_courses,
        'all_courses_count': all_courses_count,
    }





def category_context_processor(request):
    student_id = request.session.get('student_id')

    # Fetch all categories and their courses
    categories_query = """
    SELECT DISTINCT cat.id as category_id, cat.name as category_name, cat.image, 
           c.id as course_id, c.name as course_name, cat.is_free as category_is_free
    FROM categories cat
    LEFT JOIN courses c ON cat.id = c.category_id
    ORDER BY cat.name, c.name
    """
    results = execute_query(categories_query, [], fetchall=True)

    categories = {}
    for result in results:
        category_id = result['category_id']
        if category_id not in categories:
            categories[category_id] = {
                'id': category_id,
                'name': result['category_name'],
                'image': result['image'],
                'courses': []
            }
            if result['image']:
                categories[category_id]['image_url'] = os.path.join(settings.MEDIA_URL, result['image']).replace('\\', '/')
            else:
                categories[category_id]['image_url'] = os.path.join(settings.STATIC_URL, 'home_page_app/images/default-category.jpg')

        # Add course to the relevant category
        if result['course_id']:
            categories[category_id]['courses'].append({
                'id': result['course_id'],
                'name': result['course_name'],
                'category_is_free': result['category_is_free'],
            })

    # Convert categories dict to list
    categories_list = list(categories.values())

    return {
        'all_categories': categories_list,
    }



def instructors_context_processor(request):
    student_id = request.session.get('student_id')

    instructors_query = """
        SELECT 
            ins.id, 
            ins.first_name, 
            ins.last_name, 
            ins.department, 
            prof.profile_picture, 
            prof.bio, 
            AVG(rev.rating) as average_rating, 
            COUNT(DISTINCT crs.id) as total_courses, 
            COUNT(DISTINCT enr.student_id) as total_students,
            EXISTS(
                SELECT 1 
                FROM enrollments enr 
                JOIN courses crs ON enr.course_id = crs.id 
                WHERE crs.instructor_id = ins.id AND enr.student_id = %s
            ) AS is_enrolled_instructor
        FROM 
            instructors ins
        JOIN 
            profiles prof ON ins.id = prof.user_id
        LEFT JOIN 
            courses crs ON ins.id = crs.instructor_id
        LEFT JOIN 
            enrollments enr ON crs.id = enr.course_id
        LEFT JOIN 
            reviews rev ON crs.id = rev.course_id
        GROUP BY 
            ins.id
    """
    
    instructors = execute_query(instructors_query, [student_id], fetchall=True)

    for instructor in instructors:
        instructor['image_url'] = os.path.join(settings.MEDIA_URL, instructor['profile_picture']).replace('\\', '/') if instructor['profile_picture'] else os.path.join(settings.STATIC_URL, 'home_page_app/images/avatar-placeholder.jpg')
        instructor['average_rating'] = instructor['average_rating'] or 0
        instructor['full_stars'] = range(int(instructor['average_rating']))
        instructor['half_star'] = instructor['average_rating'] % 1 >= 0.5
        instructor['empty_stars'] = range(5 - int(instructor['average_rating']) - int(instructor['half_star']))

    return {
        'instructors': instructors,
        'instructor_counts': len(instructors),
    }




def instructor_rating_display(request):
    # Ensure the instructor_id is available in the request context
    course_id = request.resolver_match.kwargs.get('course_id')
    if not course_id:
        return {}

    # Fetch instructor ID based on the course ID
    instructor_id_query = """
        SELECT instructor_id
        FROM courses
        WHERE id = %s
    """
    instructor_data = execute_query(instructor_id_query, [course_id], fetchone=True)

    if not instructor_data or not instructor_data['instructor_id']:
        return {}

    instructor_id = instructor_data['instructor_id']

    # Fetch reviews related to the instructor's courses
    instructor_reviews_query = """
        SELECT AVG(r.rating) as average_rating
        FROM reviews r
        JOIN courses c ON r.course_id = c.id
        WHERE c.instructor_id = %s
    """
    instructor_rating = execute_query(instructor_reviews_query, [instructor_id], fetchone=True)
    
    # Ensure that the rating is scaled correctly
    if instructor_rating and instructor_rating['average_rating']:
        instructor_rating_display = "{:.1f}".format(instructor_rating['average_rating'] / 20)  # Convert to a 5-point scale
    else:
        instructor_rating_display = "No ratings yet"

    return {
        'instructor_rating_display': instructor_rating_display
    }


def certificates_context_processor(request):
    student_id = request.session.get('student_id')

    if not student_id:
        return {'certificates': []}

    certificates_query = """
        SELECT c.id, c.issue_date, cr.name as course_name, cr.id as course_id
        FROM certificates c
        JOIN courses cr ON c.course_id = cr.id
        WHERE c.student_id = %s
    """
    certificates = execute_query(certificates_query, [student_id], fetchall=True)

    for certificate in certificates:
        certificate_filename = f"certificate_{student_id}_{certificate['course_id']}.pdf"  # Use course_id for consistency
        certificate_path = os.path.join(settings.MEDIA_ROOT, certificate_filename)
        certificate_url = os.path.join(settings.MEDIA_URL, certificate_filename)

        if os.path.exists(certificate_path):  # Check if the file exists
            certificate['download_url'] = certificate_url
        else:
            certificate['download_url'] = None  # Handle the case where the file doesn't exist

        certificate['title'] = f"Certificate for {certificate['course_name']}"
        certificate['date_issued'] = certificate['issue_date'].strftime('%B %d, %Y')

    return {
        'certificates': certificates,
    }



def reviews_context_processor(request):
    student_id = request.session.get('student_id')

    reviews_query = """
        SELECT 
            r.id, 
            r.review_text, 
            r.rating, 
            r.created_at, 
            c.name as course_name, 
            c.image as course_image,
            s.first_name, 
            s.middle_name,
            s.last_name,
            p.profile_picture as student_profile_picture,
            r.student_id = %s AS is_student_review
        FROM 
            reviews r
        JOIN 
            courses c ON r.course_id = c.id
        JOIN 
            students s ON r.student_id = s.id
        LEFT JOIN 
            profiles p ON s.id = p.user_id AND p.user_type = 'student'
        ORDER BY 
            r.created_at DESC
    """
    
    reviews = execute_query(reviews_query, [student_id], fetchall=True)

    for review in reviews:
        review['time_ago'] = timesince(review['created_at'], now=datetime.now()) + ' ago'
        review['student_profile_image_url'] = (
            f"/media/{review['student_profile_picture']}" 
            if review['student_profile_picture'] 
            else '/static/home_page_app/images/avatar-placeholder.jpg'
        )
        review['course_image_url'] = (
            f"/media/{review['course_image']}" 
            if review['course_image'] 
            else '/static/home_page_app/images/courses/courses-8.jpg'
        )
        if not review['is_student_review']:
            review['student_name'] = f"{review['first_name']} {review['middle_name']}"

    return {
        'reviews': reviews,
    }




def payments_context_processor(request):
    student_id = request.session.get('student_id')
    
    if not student_id:
        return {'purchases': []}

    payments_query = """
        SELECT p.*, c.name as course_name, c.image as course_image
        FROM payments p
        JOIN courses c ON p.course_id = c.id
        WHERE p.student_id = %s
    """
    purchases = execute_query(payments_query, [student_id], fetchall=True)

    for purchase in purchases:
        # Construct full media URL for the course image
        if purchase['course_image']:
            purchase['course_image_url'] = f'/media/{purchase["course_image"]}'
        else:
            purchase['course_image_url'] = '/static/home_page_app/images/courses/courses-8.jpg'  # Fallback image

    return {
        'purchases': purchases,
    }




def faq_context_processor(request):
    faq_query = """
        SELECT id, question, answer, video_url, created_at 
        FROM faqs 
        ORDER BY created_at DESC 
        LIMIT 5
    """
    faqs = execute_query(faq_query, fetchall=True)

    return {
        'faqs': faqs,
    }


def event_context_processor(request):
    
    # Get the latest event
    latest_event_query = """
        SELECT * FROM events ORDER BY event_date DESC LIMIT 1
    """
    latest_event = execute_query(latest_event_query, fetchone=True)


    # Returning context
    return {
        'latest_event': latest_event,
    }
