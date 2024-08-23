from django.shortcuts import redirect
from django.urls import reverse
import re


class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that do not require admin authentication
        admin_public_paths = [
            reverse('account_app:admin_login'),  # Path to the admin login page
            reverse('account_app:admin_register'),  # Path to admin registration if it exists
            # reverse('account_app:reset_password'),  # Path to reset password
            # reverse('account_app:email_sent_confirmation'),  # Path for email sent confirmation
            # reverse('account_app:password_reset_done'),  # Path for password reset done
        ]

        # Paths that may contain dynamic segments (e.g., token)
        # dynamic_paths = [
        #     re.compile(r'^/account/password_reset_form/[^/]+/[^/]+/$'),
        # ]

        # Check if the requested path is in public paths or matches any dynamic pattern
        if request.path in admin_public_paths:
            return self.get_response(request)

        # Restrict access to the admin dashboard if not logged in as an admin it starts for admin every next path
        

        if request.path.startswith('/admin/'):
            if not request.session.get('admin_id'):
                return redirect(reverse('account_app:admin_login'))

        return self.get_response(request)