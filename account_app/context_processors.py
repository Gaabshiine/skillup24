from .utils import execute_query  # Import the execute_query function
from django.conf import settings  # Import the settings module
import os  # Import the os module

def instructor_context(request):
    """
    Provides context variables for instructor users.
    """
    instructor_user = None
    instructor_profile_picture_url = None
    instructor_cover_photo_url = None

    if 'instructor_id' in request.session:
        query = "SELECT * FROM instructors WHERE id = %s"
        instructor_user = execute_query(query, [request.session['instructor_id']], fetchone=True)

    courses = []
    if instructor_user:
        # Fetch instructor's courses
        courses_query = "SELECT * FROM courses WHERE instructor_id = %s"
        courses = execute_query(courses_query, [instructor_user['id']], fetchall=True)

        # Fetch instructor's profile
        profile_query = "SELECT * FROM profiles WHERE user_id = %s AND user_type = 'instructor'"
        profile = execute_query(profile_query, [instructor_user['id']], fetchone=True)
        
        if profile:
            # Profile picture URL
            profile_picture = profile.get('profile_picture')
            if profile_picture:
                instructor_profile_picture_url = os.path.join(settings.MEDIA_URL, profile_picture).replace('\\', '/')
            
            # Cover photo URL
            cover_photo = profile.get('cover_photo')
            if cover_photo:
                instructor_cover_photo_url = os.path.join(settings.MEDIA_URL, cover_photo).replace('\\', '/')

    return {
        'instructor_user': instructor_user,
        'courses': courses,
        'instructor_profile_picture_url': instructor_profile_picture_url,
        'instructor_cover_photo_url': instructor_cover_photo_url
    }

def student_context(request):
    student_user = None
    student_profile_picture_url = None
    student_cover_photo_url = None

    # Check if student_id is in session
    if 'student_id' in request.session:
        student_id = request.session['student_id']
        query = "SELECT * FROM students WHERE id = %s"
        student_user = execute_query(query, [student_id], fetchone=True)

        if student_user:
            profile_query = "SELECT * FROM profiles WHERE user_id = %s AND user_type = 'student'"
            profile = execute_query(profile_query, [student_user['id']], fetchone=True)
            if profile:
                # Profile picture URL
                profile_picture = profile.get('profile_picture')
                if profile_picture:
                    student_profile_picture_url = os.path.join(settings.MEDIA_URL, profile_picture).replace('\\', '/')
                
                # Cover photo URL
                cover_photo = profile.get('cover_photo')
                if cover_photo:
                    student_cover_photo_url = os.path.join(settings.MEDIA_URL, cover_photo).replace('\\', '/')

    return {
        'student_user': student_user,
        'student_profile_picture_url': student_profile_picture_url,
        'student_cover_photo_url': student_cover_photo_url,
    }


