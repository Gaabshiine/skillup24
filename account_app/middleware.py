# middleware.py

from django.shortcuts import redirect
from django.urls import reverse
import re


class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that do not require login
        user_public_paths = [
            reverse('home_page_app:home'),
            reverse('home_page_app:about'),
            reverse('home_page_app:contact'),
            reverse('home_page_app:event_list'),
            reverse('home_page_app:event_detail', args=[1]),  # Dynamic args handled separately
            reverse('home_page_app:zoom_meeting_list'),
            reverse('home_page_app:zoom_meeting_detail', args=[1]),  # Dynamic args handled separately
            reverse('home_page_app:course_list'),
            reverse('home_page_app:course_detail', args=[1]),  # Dynamic args handled separately
            reverse('home_page_app:course_category', args=[1]),  # Dynamic args handled separately
            reverse('home_page_app:instructor_list'),
            reverse('home_page_app:instructor_detail', args=[1]),  # Dynamic args handled separately
            reverse('home_page_app:sitemap'),  # Sitemap should be public
            reverse('account_app:login'),
            reverse('account_app:admin_login'),
            reverse('account_app:add_admin'),
            reverse('account_app:admin_register'),
            reverse('account_app:add_student_by_user'),
            reverse('account_app:add_student_from_slider'),
            reverse('account_app:model_login'),
            reverse('account_app:reset_password_request'),
            # Add other paths that should be accessible without login
        ]

        dynamic_skip_patterns = [
            re.compile(r'^/account/reset_password/[^/]+/[^/]+/$'),
        ]

        if request.path in user_public_paths or any(pattern.match(request.path) for pattern in dynamic_skip_patterns):
            return self.get_response(request)

        # Check if request path requires login
        if request.path.startswith('/account/') or request.path.startswith('/student_dashboard/') or request.path in self.protected_paths() or request.path.startswith('/enrolled_courses/'):
            if not request.session.get('student_id') and not request.session.get('admin_id'):
                return redirect(reverse('account_app:login'))

        return self.get_response(request)

    def protected_paths(self):
        return [
            reverse('home_page_app:submit_review', args=[1]),  # Protects review submission
            reverse('home_page_app:purchase', args=[1]),  # Protects purchase page
            reverse('home_page_app:submit_payment'),  # Protects payment submission
            reverse('home_page_app:payment_confirmation'),  # Protects payment confirmation
            reverse('home_page_app:complete_lesson'),  # Protects lesson completion
            
            # Add more paths that need protection
        ]