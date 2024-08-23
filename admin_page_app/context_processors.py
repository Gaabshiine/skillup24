from .utils import execute_query  # Import the execute_query function
from django.conf import settings  # Import the settings module
import os  # Import the os module


def admin_context(request):
    """
    Provides context variables for admin users.
    """

    # Check if there is at least one admin in the database
    query = "SELECT COUNT(*) as admin_count FROM admins"
    result = execute_query(query, [], fetchone=True)

    # Determine if any admins are present
    admin_exists = result['admin_count'] > 0

    admin_user = None
    admin_profile_picture_url = None

    if 'admin_id' in request.session:
        admin_id = request.session['admin_id']
        query = "SELECT * FROM admins WHERE id = %s"
        admin_user = execute_query(query, [admin_id], fetchone=True)
        if admin_user:
            profile_query = "SELECT * FROM profiles WHERE user_id = %s AND user_type = 'admin'"
            profile = execute_query(profile_query, [admin_user['id']], fetchone=True)
            if profile:
                # Check if profile picture exists before constructing URL
                profile_picture = profile.get('profile_picture')
                if profile_picture:
                    admin_profile_picture_url = os.path.join(settings.MEDIA_URL, profile_picture).replace('\\', '/')
        
    return {
        'admin_user': admin_user,
        'admin_profile_picture_url': admin_profile_picture_url,
        'admin_exists': admin_exists,
    }
    