from django.shortcuts import render,redirect
from django.urls import reverse
from .utils import execute_query, extract_user_data, hash_password, update_user_data
from django.contrib import messages
from django.contrib.auth.hashers import check_password
import os
from django.db import IntegrityError
from django.conf import settings
from django.http import JsonResponse
from datetime import datetime
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db import IntegrityError
import logging
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from .tokens import account_activation_token
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .models import Student, Instructor, Admin, Profile
from home_page_app.views import generate_certificate_pdf



logger = logging.getLogger(__name__)


# Create your views here.



# -----------------------------------------------------> 1) Start: Regiseration Management <-----------------------------------------------------

# 1.1) Add Student by Admin
def add_student_by_admin(request):
    if request.method == 'POST':
        data, errors = extract_user_data(request)

        # Check for validation errors and return them as a JSON response
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        if not data['password']:
            return JsonResponse({'success': False, 'error': 'Password is required.'})

        if not data['email_address']:
            return JsonResponse({'success': False, 'error': 'Email address is required.'})

        data['password'] = hash_password(data['password'])  # Hash the password

        query = """
            INSERT INTO students (first_name, middle_name, last_name, email_address, password, phone_number, gender, date_of_birth, address, major, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [
            data['first_name'], data['middle_name'], data['last_name'],
            data['email_address'], data['password'], data['phone_number'],
            data['gender'], data['date_of_birth'], data['address'], data['major']
        ]
        
        # Execute the query to insert data into the database
        execute_query(query, params)

        # Return a JSON response indicating success, using reverse to get the URL
        return JsonResponse({
            'success': True,
            'message': 'Student added successfully by admin!',
            'redirect_url': reverse('admin_page_app:student_list')  # Use the name of the URL
        })

    # Render the HTML form if not a POST request
    return render(request, 'account_app/admin_student_register.html')



# 1.2) Add Student by User
def add_student_by_user(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Extract user data and validate
        data, errors = extract_user_data(request)

        if errors:
            # Return errors as JSON
            return JsonResponse({'success': False, 'errors': errors})

        # Hash the password
        data['password'] = hash_password(data['password'])

        # Insert the new student into the database
        query = """
            INSERT INTO students (first_name, middle_name, last_name, email_address, password, phone_number, gender, date_of_birth, address, major, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [
            data['first_name'], data['middle_name'], data['last_name'],
            data['email_address'], data['password'], data['phone_number'],
            data['gender'], data['date_of_birth'], data['address'], data['major']
        ]

        try:
            execute_query(query, params)
            # Return success response
            return JsonResponse({'success': True, 'redirect_url': reverse('account_app:login')})
        except Exception as e:
            # Handle database errors
            return JsonResponse({'success': False, 'error': 'An error occurred while registering the student.'})

    return JsonResponse({'success': False, 'error': 'Invalid request.'})


# 1.3) Add Student from Slider or another form of registration
def add_student_from_slider(request):
    if request.method == 'POST':
        # Extract data directly from POST
        data = {
            'first_name': request.POST.get('first_name', '').strip(),
            'middle_name': request.POST.get('middle_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'email_address': request.POST.get('email_address', '').strip(),
            'password': request.POST.get('password', ''),
            'confirm_password': request.POST.get('confirm_password', ''),
            'phone_number': request.POST.get('phone_number', '').strip(),
            'gender': request.POST.get('gender', '').strip(),
            'date_of_birth': request.POST.get('date_of_birth', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'major': request.POST.get('major_or_department', '').strip(),
            'terms': request.POST.get('terms', '')  # Checkbox value
        }

        # Validate fields
        errors = {}

        # First name validation
        if not data['first_name']:
            errors['first_name'] = 'First name is required.'
        elif not data['first_name'].replace(' ', '').isalpha():
            errors['first_name'] = 'First name must be alphabetic.'

        # Middle name validation
        if not data['middle_name']:
            errors['middle_name'] = 'Middle name is required.'
        elif not data['middle_name'].replace(' ', '').isalpha():
            errors['middle_name'] = 'Middle name must be alphabetic.'

        # Last name validation
        if not data['last_name']:
            errors['last_name'] = 'Last name is required.'
        elif not data['last_name'].replace(' ', '').isalpha():
            errors['last_name'] = 'Last name must be alphabetic.'

        # Phone number validation
        if not data['phone_number']:
            errors['phone_number'] = 'Phone number is required.'

        # Gender validation
        if not data['gender']:
            errors['gender'] = 'Gender is required.'

        # Date of birth validation
        if not data['date_of_birth']:
            errors['date_of_birth'] = 'Date of birth is required.'
        else:
            try:
                dob = parse_date(data['date_of_birth'])
                if dob is None:
                    raise ValueError("Invalid date format")
                age = (datetime.now().date() - dob).days // 365
                if age < 10:
                    errors['date_of_birth'] = 'Age must be greater than 10 years.'
            except ValueError:
                errors['date_of_birth'] = 'Invalid date of birth format.'

        # Address validation
        if not data['address']:
            errors['address'] = 'Address is required.'

        # Major validation
        if not data['major']:
            errors['major'] = 'Major is required.'

        # Email validation
        if not data['email_address']:
            errors['email_address'] = 'Email address is required.'
        else:
            # Check email uniqueness
            query = "SELECT * FROM students WHERE email_address = %s"
            student = execute_query(query, [data['email_address']], fetchone=True)
            if student:
                errors['email_address'] = 'Email address already exists.'

        # Password validation
        if not data['password']:
            errors['password'] = 'Password is required.'
        elif len(data['password']) < 8:
            errors['password'] = 'Password must be at least 8 characters long.'

        # Confirm password validation
        if data['confirm_password'] != data['password']:
            errors['confirm_password'] = 'Passwords do not match.'

        # Terms acceptance validation
        if data['terms'] != 'on':
            errors['terms'] = 'You must accept the terms and conditions.'

        # Check for errors and respond accordingly
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        # Hash the password
        data['password'] = hash_password(data['password'])

        # Insert the new student into the database
        query = """
            INSERT INTO students (first_name, middle_name, last_name, email_address, password, phone_number, gender, date_of_birth, address, major, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [
            data['first_name'], data['middle_name'], data['last_name'],
            data['email_address'], data['password'], data['phone_number'],
            data['gender'], data['date_of_birth'], data['address'], data['major']
        ]

        try:
            execute_query(query, params)
            return JsonResponse({'success': True, 'message': 'Student registered successfully!', 'redirect_url': reverse('account_app:login')})
        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': 'An error occurred while registering the student: ' + str(e)}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred: ' + str(e)}, status=500)

    return render(request, 'account_app/slider_student_register.html')


# 1.4) Add Instructor by Admin
def add_instructor_by_admin(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Extract data from the POST request
        data = {
            'first_name': request.POST.get('first_name', '').strip(),
            'middle_name': request.POST.get('middle_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'email_address': request.POST.get('email_address', '').strip().lower(),
            'password': request.POST.get('password', ''),
            'confirm_password': request.POST.get('confirm_password', ''),
            'phone_number': request.POST.get('phone_number', '').strip(),
            'gender': request.POST.get('gender', '').strip(),
            'date_of_birth': request.POST.get('date_of_birth', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'department': request.POST.get('major_or_department', '').strip()
        }

        # Perform validation
        errors = {}

        # Validate names
        if not data['first_name']:
            errors['first_name'] = 'First name is required.'
        elif not data['first_name'].replace(' ', '').isalpha():
            errors['first_name'] = 'First name must be alphabetic.'

        if not data['middle_name']:
            errors['middle_name'] = 'Middle name is required.'
        elif not data['middle_name'].replace(' ', '').isalpha():
            errors['middle_name'] = 'Middle name must be alphabetic.'

        if not data['last_name']:
            errors['last_name'] = 'Last name is required.'
        elif not data['last_name'].replace(' ', '').isalpha():
            errors['last_name'] = 'Last name must be alphabetic.'

        # Validate email
        if not data['email_address']:
            errors['email_address'] = 'Email address is required.'
        else:
            query = "SELECT * FROM instructors WHERE email_address = %s"
            instructor = execute_query(query, [data['email_address']], fetchone=True)
            if instructor:
                errors['email_address'] = 'Email address already exists.'

        # Validate password
        if not data['password']:
            errors['password'] = 'Password is required.'
        elif len(data['password']) < 8:
            errors['password'] = 'Password must be at least 8 characters long.'
        elif data['password'] != data['confirm_password']:
            errors['confirm_password'] = 'Passwords do not match.'

        # Validate phone number
        if not data['phone_number']:
            errors['phone_number'] = 'Phone number is required.'

        # Validate gender
        if not data['gender']:
            errors['gender'] = 'Gender is required.'

        # Validate date of birth and age
        if not data['date_of_birth']:
            errors['date_of_birth'] = 'Date of birth is required.'
        else:
            try:
                dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                today = timezone.now().date()
                age = (today - dob).days // 365
                if age < 18:
                    errors['date_of_birth'] = 'Age must be 18 years or older to register.'
            except ValueError:
                errors['date_of_birth'] = 'Invalid date of birth format.'

        # Validate address
        if not data['address']:
            errors['address'] = 'Address is required.'

        # Validate department
        if not data['department']:
            errors['department'] = 'Department is required.'

        # Return errors if any
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Hash the password before storing it
        hashed_password = hash_password(data['password'])

        # Insert instructor data into the database
        query = """
            INSERT INTO instructors (
                first_name, middle_name, last_name, email_address, password,
                phone_number, gender, date_of_birth, address, department, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [
            data['first_name'], data['middle_name'], data['last_name'],
            data['email_address'], hashed_password, data['phone_number'],
            data['gender'], data['date_of_birth'], data['address'],
            data['department']
        ]
        
        execute_query(query, params)

        # Return a success response
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('admin_page_app:instructor_list')
        })

    return render(request, 'account_app/admin_instructor_register.html')

# 1.5) Add Admin
def admin_register_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Extract data from the POST request
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email_address = request.POST.get('email_address', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        phone_number = request.POST.get('phone_number', '').strip()
        gender = request.POST.get('gender', '').strip()
        date_of_birth_str = request.POST.get('date_of_birth', '').strip()
        address = request.POST.get('address', '').strip()

        # Validate the data
        errors = {}

        # Validate names
        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not middle_name:
            errors['middle_name'] = 'Middle name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'

        # Validate email
        if not email_address:
            errors['email_address'] = 'Email address is required.'
        else:
            query = "SELECT * FROM admins WHERE email_address = %s"
            existing_admin = execute_query(query, [email_address], fetchone=True)
            if existing_admin:
                errors['email_address'] = 'Email address is already in use.'

        # Validate password
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters long.'

        # Validate confirm password
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        # Validate phone number
        if not phone_number:
            errors['phone_number'] = 'Phone number is required.'

        # Validate gender
        if gender not in ['male', 'female']:
            errors['gender'] = 'Invalid gender selected.'

        # Validate date of birth and check if age is 18 or older
        if not date_of_birth_str:
            errors['date_of_birth'] = 'Date of birth is required.'
        else:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                today = timezone.now().date()
                age = (today - date_of_birth).days // 365
                if age < 18:
                    errors['date_of_birth'] = 'You must be at least 18 years old to register.'
            except ValueError:
                errors['date_of_birth'] = 'Invalid date of birth format.'

        # Validate address
        if not address:
            errors['address'] = 'Address is required.'

        # Return errors if any
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # If no errors, create the admin using raw SQL query
        hashed_password = hash_password(password)
        insert_query = """
            INSERT INTO admins (first_name, middle_name, last_name, email_address, password, phone_number, gender, date_of_birth, address, is_admin, is_staff, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [first_name, middle_name, last_name, email_address, hashed_password, phone_number, gender, date_of_birth, address, True, True]

        try:
            execute_query(insert_query, params)
            # Successful creation, return success response
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('admin_page_app:view_admins')  # Redirect to view admins page
            })
        except IntegrityError as e:
            # Log the error for further analysis
            print(f"IntegrityError: {e}")
            return JsonResponse({'success': False, 'error': 'An error occurred while registering the admin.'})
        except Exception as e:
            # Log unexpected errors
            print(f"Unexpected error: {e}")
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again.'})

    # If not a POST request, just render the registration page
    return render(request, 'account_app/admin_register.html')


# 1.6) Add Admin from Slider or another form of registration that are out side of the dasbhboard
def admin_register_view_without_login(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Extract data from the POST request
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email_address = request.POST.get('email_address', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        phone_number = request.POST.get('phone_number', '').strip()
        gender = request.POST.get('gender', '').strip()
        date_of_birth_str = request.POST.get('date_of_birth', '').strip()
        address = request.POST.get('address', '').strip()

        # Validate the data
        errors = {}

        # Validate names
        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not middle_name:
            errors['middle_name'] = 'Middle name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'

        # Validate email
        if not email_address:
            errors['email_address'] = 'Email address is required.'
        else:
            query = "SELECT * FROM admins WHERE email_address = %s"
            existing_admin = execute_query(query, [email_address], fetchone=True)
            if existing_admin:
                errors['email_address'] = 'Email address is already in use.'

        # Validate password
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters long.'

        # Validate confirm password
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        # Validate phone number
        if not phone_number:
            errors['phone_number'] = 'Phone number is required.'

        # Validate gender
        if gender not in ['male', 'female']:
            errors['gender'] = 'Invalid gender selected.'

        # Validate date of birth and check if age is 18 or older
        if not date_of_birth_str:
            errors['date_of_birth'] = 'Date of birth is required.'
        else:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                today = timezone.now().date()
                age = (today - date_of_birth).days // 365
                if age < 18:
                    errors['date_of_birth'] = 'You must be at least 18 years old to register.'
            except ValueError:
                errors['date_of_birth'] = 'Invalid date of birth format.'

        # Validate address
        if not address:
            errors['address'] = 'Address is required.'

        # Return errors if any
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # If no errors, create the admin using raw SQL query
        hashed_password = hash_password(password)
        insert_query = """
            INSERT INTO admins (first_name, middle_name, last_name, email_address, password, phone_number, gender, date_of_birth, address, is_admin, is_staff, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [first_name, middle_name, last_name, email_address, hashed_password, phone_number, gender, date_of_birth, address, True, True]

        try:
            execute_query(insert_query, params)
            # Successful creation, return success response
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('admin_page_app:dashboard')  # Redirect to dashboard page
            })
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'An error occurred while registering the admin.'})

    # If not a POST request, just render the registration page
    return render(request, 'account_app/admin_register_withoutlogin.html')


# -----------------------------------------------------> End: Regiseration Management <-----------------------------------------------------




# -----------------------------------------------------> 3) Start: Delete Users <-----------------------------------------------------

# 3.1) delete instructor and his profile by using sql query as prvious
def delete_instructor(request, id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            instructor = Instructor.objects.filter(id=id).first()
            if instructor:
                instructor.delete()  # This will cascade delete all related data

                # If there are any additional custom deletion operations:
                Profile.objects.filter(user_id=id, user_type='instructor').delete()

                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Instructor not found or already deleted.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method or headers.'})


# 3.2) delete student 
def delete_student(request, id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            student = Student.objects.filter(id=id).first()
            if student:
                student.delete()  # This will cascade delete all related data

                # If there are any additional custom deletion operations:
                Profile.objects.filter(user_id=id, user_type='student').delete()

                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Student not found or already deleted.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method or headers.'})


# 3.3) delete admin
def delete_admin(request, id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            admin = Admin.objects.filter(id=id).first()
            if admin:
                admin.delete()  # This will cascade delete all related data

                # If there are any additional custom deletion operations:
                Profile.objects.filter(user_id=id, user_type='admin').delete()

                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Admin not found or already deleted.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method or headers.'})

# -----------------------------------------------------> End: Delete Users <-----------------------------------------------------




# -----------------------------------------------------> 2) Start: Login Management <-----------------------------------------------------

# 2.1)Login View
def model_login_view(request):
    if request.method == 'POST':
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')

        # Validate email and password presence
        if not email_address or not password:
            return JsonResponse({'success': False, 'error': 'Email and password are required.'})

        # Fetch the user by email
        query = "SELECT * FROM students WHERE email_address = %s"
        student = execute_query(query, [email_address], fetchone=True)

        if student and check_password(password, student['password']):
            # Successful login, set session or other login mechanisms
            request.session['student_id'] = student['id']
            return JsonResponse({'success': True, 'redirect_url': reverse('home_page_app:student_dashboard', args=[student['id']])})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid email or password.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def login_view(request):
    if request.method == 'POST':
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')

        # Validate email and password presence
        if not email_address or not password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Email and password are required.'})
            else:
                messages.error(request, 'Email and password are required.')
                return render(request, 'account_app/another_login_page.html')

        # Fetch the user by email
        query = "SELECT * FROM students WHERE email_address = %s"
        student = execute_query(query, [email_address], fetchone=True)

        if student and check_password(password, student['password']):
            # Successful login, set session or other login mechanisms
            request.session['student_id'] = student['id']
            student_id = student['id']
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': reverse('home_page_app:student_dashboard', args=[student_id])})
            else:
                messages.success(request, 'Login successful!')
                return redirect(reverse('home_page_app:student_dashboard', args=[student_id]))
        else:
            messages.error(request, 'Invalid email or password.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid email or password.'})
            else:
                messages.error(request, 'Invalid email or password.')

    return render(request, 'account_app/another_login_page.html')

def admin_login_view(request):
    if request.method == 'POST':
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')

        # Validate email and password presence
        if not email_address or not password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Email and password are required.'})
            else:
                messages.error(request, 'Email and password are required.')
                return render(request, 'account_app/admin_login.html')

        # Fetch the admin by email
        query = "SELECT * FROM admins WHERE email_address = %s"
        admin = execute_query(query, [email_address], fetchone=True)

        if admin and check_password(password, admin['password']):
            # Successful login, set session or other login mechanisms
            request.session['admin_id'] = admin['id']
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': reverse('admin_page_app:dashboard')})
            else:
                messages.success(request, 'Login successful!')
                return redirect(reverse('admin_page_app:dashboard'))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid email or password.'})
            else:
                messages.error(request, 'Invalid email or password.')

    return render(request, 'account_app/admin_login.html')

# 2.2) admin_logout
def admin_logout_view(request):
    # Destroy the session completely
    request.session.flush()
    return redirect('account_app:admin_login')


# 2.3) student_logout
def student_logout_view(request):
    # Destroy the session completely
    request.session.flush()
    return redirect('account_app:login')

   


# -----------------------------------------------------> End: Login Management <-----------------------------------------------------




# -----------------------------------------------------> 3) Start: Reset Password <-----------------------------------------------------

# 3.1) Function to send reset email
def send_reset_email(user, reset_link):
    subject = "Password Reset Requested"
    message = (
        f"Hi {user['first_name']},\n\n"
        "You recently requested to reset your password for your account. "
        "Click the link below to reset it:\n\n"
        f"{reset_link}\n\n"
        "If you did not request a password reset, please ignore this email or contact support if you have questions.\n\n"
        "Thanks,\n"
        "Skillup24 Team"
    )
    send_mail(subject, message, 'noreply@skillup24.onrender.com', [user['email_address']])

# 3.2) Reset Password Request View
def reset_password_request_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        email_address = request.POST.get('email_address', '').strip()
        if not email_address:
            return JsonResponse({'success': False, 'errors': {'email_address': 'Email is required.'}})
        
        query = "SELECT * FROM students WHERE email_address = %s"
        student = execute_query(query, [email_address], fetchone=True)
        
        if student:
            uid = urlsafe_base64_encode(force_bytes(student['id']))
            token = account_activation_token.make_token(student)
            reset_link = reverse('account_app:reset_password', kwargs={'uidb64': uid, 'token': token})
            reset_link = f"http://{get_current_site(request).domain}{reset_link}"
            
            send_reset_email(student, reset_link)

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': {'email_address': 'No user found with this email address.'}})

    return render(request, 'account_app/reset_password_request.html')

# 3.3) Reset Password View
def reset_password_view(request, uidb64, token):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            query = "SELECT * FROM students WHERE id = %s"
            student = execute_query(query, [uid], fetchone=True)
        except (TypeError, ValueError, OverflowError):
            student = None

        if student and account_activation_token.check_token(student, token):
            password = request.POST.get('password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            errors = {}
            if not password:
                errors['password'] = 'Password is required.'
            if password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match.'

            if errors:
                return JsonResponse({'success': False, 'errors': errors})

            hashed_password = hash_password(password)
            update_query = "UPDATE students SET password = %s WHERE id = %s"
            execute_query(update_query, [hashed_password, student['id']])

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'The reset link is invalid or has expired.'})

    return render(request, 'account_app/reset_password.html', {'uidb64': uidb64, 'token': token})


# -----------------------------------------------------> End: Reset Password <-----------------------------------------------------





# -----------------------------------------------------> 3) Start: Student Profile Management <-----------------------------------------------------
# 4.1) Update Student and Profile
def update_student_and_profile_by_user(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return JsonResponse({'success': False, 'redirect_url': reverse('account_app:login')})

    if request.method == 'POST':
        data, errors = update_user_data(request)  # Assuming this function processes the form data and returns any errors

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Check if the name has changed
        student_before_update = execute_query("SELECT first_name, middle_name, last_name FROM students WHERE id = %s", [student_id], fetchone=True)
        name_changed = (
            student_before_update['first_name'] != data['first_name'] or
            student_before_update['middle_name'] != data['middle_name'] or
            student_before_update['last_name'] != data['last_name']
        )

        # Update student data
        query = """
            UPDATE students SET first_name=%s, middle_name=%s, last_name=%s, phone_number=%s, gender=%s, date_of_birth=%s, address=%s, major=%s, created_at=NOW()
            WHERE id=%s
        """
        params = [data['first_name'], data['middle_name'], data['last_name'], data['phone_number'], data['gender'], data['date_of_birth'], data['address'], data['major'], student_id]
        execute_query(query, params)

        # Update or regenerate certificates if the name changed
        if name_changed:
            certificates_query = "SELECT id, course_id FROM certificates WHERE student_id = %s"
            certificates = execute_query(certificates_query, [student_id], fetchall=True)

            for certificate in certificates:
                certificate_filename = f"certificate_{student_id}_{certificate['course_id']}.pdf"
                certificate_path = os.path.join(settings.MEDIA_ROOT, certificate_filename)
                generate_certificate_pdf(certificate_path, student_id, certificate['course_id'])

        # Prepare profile data
        profile_data = {
            'bio': data['bio'],
            'facebook': data['facebook'],
            'twitter': data['twitter'],
            'linkedIn': data['linkedIn'],
            'github': data['github'],
            'user_type': 'student',
            'user_id': student_id
        }

        # Handle profile picture
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture:
            profile_picture_path = os.path.join('profile_images', profile_picture.name)
            with open(os.path.join(settings.MEDIA_ROOT, profile_picture_path), 'wb+') as destination:
                for chunk in profile_picture.chunks():
                    destination.write(chunk)
            profile_data['profile_picture'] = profile_picture_path
        else:
            profile = execute_query("SELECT profile_picture FROM profiles WHERE user_id = %s AND user_type = 'student'", [student_id], fetchone=True)
            if profile:
                profile_data['profile_picture'] = profile['profile_picture']

        # Handle cover photo
        cover_photo = request.FILES.get('cover_photo')
        if cover_photo:
            cover_photo_path = os.path.join('cover_images', cover_photo.name)
            with open(os.path.join(settings.MEDIA_ROOT, cover_photo_path), 'wb+') as destination:
                for chunk in cover_photo.chunks():
                    destination.write(chunk)
            profile_data['cover_photo'] = cover_photo_path
        else:
            profile = execute_query("SELECT cover_photo FROM profiles WHERE user_id = %s AND user_type = 'student'", [student_id], fetchone=True)
            if profile:
                profile_data['cover_photo'] = profile['cover_photo']

        # Update or insert profile data
        existing_profile = execute_query(
            "SELECT COUNT(*) as count FROM profiles WHERE user_id = %s AND user_type = 'student'", [student_id], fetchone=True
        )

        if existing_profile and existing_profile['count'] > 0:
            query = """
                UPDATE profiles SET bio=%s, facebook=%s, twitter=%s, linkedIn=%s, github=%s, profile_picture=%s, cover_photo=%s, user_type=%s, user_id=%s, created_at=NOW()
                WHERE user_id=%s AND user_type='student'
            """
            params = [
                profile_data['bio'], profile_data['facebook'], profile_data['twitter'],
                profile_data['linkedIn'], profile_data['github'], profile_data.get('profile_picture'),
                profile_data.get('cover_photo'), profile_data['user_type'], profile_data['user_id'], student_id
            ]
        else:
            query = """
                INSERT INTO profiles (bio, facebook, twitter, linkedIn, github, profile_picture, cover_photo, user_type, user_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            params = [
                profile_data['bio'], profile_data['facebook'], profile_data['twitter'],
                profile_data['linkedIn'], profile_data['github'], profile_data.get('profile_picture'),
                profile_data.get('cover_photo'), profile_data['user_type'], profile_data['user_id']
            ]

        execute_query(query, params)
        return JsonResponse({'success': True, 'message': 'Student profile updated successfully!'})

    student = execute_query("SELECT * FROM students WHERE id = %s", [student_id], fetchone=True)
    profile = execute_query("SELECT * FROM profiles WHERE user_id = %s AND user_type = 'student'", [student_id], fetchone=True)

    # Format date_of_birth for HTML date input
    if student['date_of_birth']:
        student['date_of_birth'] = student['date_of_birth'].strftime('%Y-%m-%d')

    profile_picture_url = os.path.join(settings.MEDIA_URL, profile['profile_picture']).replace('\\', '/') if profile and profile.get('profile_picture') else None
    cover_photo_url = os.path.join(settings.MEDIA_URL, profile['cover_photo']).replace('\\', '/') if profile and profile.get('cover_photo') else None

    return render(request, 'account_app/user_student_update.html', {'student': student, 'profile': profile, 'profile_picture_url': profile_picture_url, 'cover_photo_url': cover_photo_url})



# 4.2) Upload Cover Photo by user
def upload_cover_photo(request):
    if request.method == 'POST':
        cover_photo = request.FILES.get('cover_photo')
        if not cover_photo:
            return JsonResponse({'error': 'No cover photo uploaded.'})

        student_id = request.session.get('student_id')
        if not student_id:
            return JsonResponse({'error': 'Student ID not found in session.'})

        # Ensure the cover_images directory exists
        cover_photo_dir = os.path.join(settings.MEDIA_ROOT, 'cover_images')
        if not os.path.exists(cover_photo_dir):
            os.makedirs(cover_photo_dir)

        cover_photo_path = os.path.join('cover_images', cover_photo.name)
        cover_photo_full_path = os.path.join(settings.MEDIA_ROOT, cover_photo_path)

        # Save the file to the cover_images directory
        with open(cover_photo_full_path, 'wb+') as destination:
            for chunk in cover_photo.chunks():
                destination.write(chunk)

        cover_photo_url = os.path.join(settings.MEDIA_URL, cover_photo_path).replace('\\', '/')

        # Check if the profile exists and update or insert
        existing_profile = execute_query(
            "SELECT COUNT(*) as count FROM profiles WHERE user_id = %s AND user_type = 'student'", [student_id], fetchone=True
        )

        if existing_profile and existing_profile['count'] > 0:
            query = """
                UPDATE profiles 
                SET cover_photo=%s, created_at=NOW()
                WHERE user_id=%s AND user_type='student'
            """
            params = [cover_photo_path, student_id]
        else:
            query = """
                INSERT INTO profiles (cover_photo, user_type, user_id, created_at) 
                VALUES (%s, 'student', %s, NOW())
            """
            params = [cover_photo_path, student_id]

        execute_query(query, params)
        return JsonResponse({'cover_photo_url': cover_photo_url})

    return JsonResponse({'error': 'Invalid request method.'})


# 4.3) Upload Profile Picture by user
def upload_profile_picture(request):
    if request.method == 'POST':
        profile_picture = request.FILES.get('profile_picture')
        if not profile_picture:
            return JsonResponse({'error': 'No profile picture uploaded.'})

        student_id = request.session.get('student_id')
        if not student_id:
            return JsonResponse({'error': 'Student ID not found in session.'})

        profile_picture_path = os.path.join('profile_images', profile_picture.name)
        with open(os.path.join(settings.MEDIA_ROOT, profile_picture_path), 'wb+') as destination:
            for chunk in profile_picture.chunks():
                destination.write(chunk)

        profile_picture_url = os.path.join(settings.MEDIA_URL, profile_picture_path).replace('\\', '/')

        existing_profile = execute_query(
            "SELECT COUNT(*) as count FROM profiles WHERE user_id = %s AND user_type = 'student'", [student_id], fetchone=True
        )

        if existing_profile and existing_profile['count'] > 0:
            query = """
                UPDATE profiles 
                SET profile_picture=%s, created_at=NOW()
                WHERE user_id=%s AND user_type='student'
            """
            params = [profile_picture_path, student_id]
        else:
            query = """
                INSERT INTO profiles (profile_picture, user_type, user_id, created_at) 
                VALUES (%s, 'student', %s, NOW())
            """
            params = [profile_picture_path, student_id]

        execute_query(query, params)
        return JsonResponse({'profile_picture_url': profile_picture_url})

    return JsonResponse({'error': 'Invalid request method.'})

# 4.4) Delete Photos by user
def delete_photos(request):
    if request.method == 'POST':
        student_id = request.session.get('student_id')
        if not student_id:
            return JsonResponse({'error': 'Student ID not found in session.'})

        photo_type = request.POST.get('photo_type')
        if photo_type not in ['profile_picture', 'cover_photo']:
            return JsonResponse({'error': 'Invalid photo type.'})

        # Fetch the current profile
        profile = execute_query(
            "SELECT profile_picture, cover_photo FROM profiles WHERE user_id = %s AND user_type = 'student'",
            [student_id],
            fetchone=True
        )

        if not profile:
            return JsonResponse({'error': 'Profile not found.'})

        # Delete the specified photo
        if photo_type == 'profile_picture':
            profile_picture_path = profile.get('profile_picture')
            if profile_picture_path:
                profile_picture_full_path = os.path.join(settings.MEDIA_ROOT, profile_picture_path)
                if os.path.exists(profile_picture_full_path):
                    os.remove(profile_picture_full_path)
                query = "UPDATE profiles SET profile_picture=NULL WHERE user_id=%s AND user_type='student'"
                execute_query(query, [student_id])
        elif photo_type == 'cover_photo':
            cover_photo_path = profile.get('cover_photo')
            if cover_photo_path:
                cover_photo_full_path = os.path.join(settings.MEDIA_ROOT, cover_photo_path)
                if os.path.exists(cover_photo_full_path):
                    os.remove(cover_photo_full_path)
                query = "UPDATE profiles SET cover_photo=NULL WHERE user_id=%s AND user_type='student'"
                execute_query(query, [student_id])

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request method.'})


# 4.5) Update Student and Profile by Admin
def update_student_and_profile_by_admin(request, student_id):
    # Fetch student data
    student_query = "SELECT * FROM students WHERE id = %s"
    student = execute_query(student_query, [student_id], fetchone=True)

    # Ensure the student exists
    if not student:
        return JsonResponse({'success': False, 'error': "Student not found."})

    # Format the date_of_birth correctly if it exists
    if student['date_of_birth']:
        student['date_of_birth'] = student['date_of_birth'].strftime('%Y-%m-%d')

    # Fetch or create the student's profile
    profile_query = "SELECT * FROM profiles WHERE user_id = %s AND user_type = 'student'"
    profile = execute_query(profile_query, [student_id], fetchone=True)

    # If profile does not exist, create it with default values
    if not profile:
        create_profile_query = """
            INSERT INTO profiles (bio, facebook, twitter, linkedIn, github, user_type, user_id, created_at)
            VALUES ('', '', '', '', '', 'student', %s, NOW())
        """
        execute_query(create_profile_query, [student_id])
        profile = execute_query(profile_query, [student_id], fetchone=True)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = request.POST
        errors = {}

        # Validate and update student details
        if not data.get('first_name'):
            errors['first_name'] = 'First name is required.'
        if not data.get('middle_name'):
            errors['middle_name'] = 'Middle name is required.'
        if not data.get('last_name'):
            errors['last_name'] = 'Last name is required.'
        if not data.get('date_of_birth'):
            errors['date_of_birth'] = 'Date of birth is required.'
        if not data.get('phone_number'):
            errors['phone_number'] = 'Phone number is required.'
        if not data.get('address'):
            errors['address'] = 'Address is required.'
        if not data.get('major'):
            errors['major'] = 'Major is required.'
        if not data.get('email_address'):
            errors['email_address'] = 'Email address is required.'

        # Age validation
        if data.get('date_of_birth'):
            try:
                dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
                age = (datetime.now().date() - dob.date()).days // 365
                if age < 18:
                    errors['date_of_birth'] = 'Student must be at least 18 years old.'
            except ValueError:
                errors['date_of_birth'] = 'Invalid date of birth format.'

        # Return errors if any
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Update student details
        student_update_query = """
            UPDATE students
            SET first_name=%s, middle_name=%s, last_name=%s, date_of_birth=%s, phone_number=%s,
                address=%s, major=%s, email_address=%s
            WHERE id=%s
        """
        student_params = [
            data.get('first_name', student['first_name']),
            data.get('middle_name', student['middle_name']),
            data.get('last_name', student['last_name']),
            data.get('date_of_birth', student['date_of_birth']),
            data.get('phone_number', student['phone_number']),
            data.get('address', student['address']),
            data.get('major', student['major']),
            data.get('email_address', student['email_address']),
            student_id
        ]

        execute_query(student_update_query, student_params)

        # Update profile details
        profile_data = {
            'bio': data.get('bio', profile['bio']),
            'facebook': data.get('facebook', profile['facebook']),
            'twitter': data.get('twitter', profile['twitter']),
            'linkedIn': data.get('linkedIn', profile['linkedIn']),
            'github': data.get('github', profile['github']),
            'user_id': student_id
        }

        # Check for new profile picture
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture:
            profile_picture_path = os.path.join('profile_images', profile_picture.name)
            with open(os.path.join(settings.MEDIA_ROOT, profile_picture_path), 'wb+') as destination:
                for chunk in profile_picture.chunks():
                    destination.write(chunk)
            profile_data['profile_picture'] = profile_picture_path
        else:
            profile_data['profile_picture'] = profile['profile_picture']

        # Check for new cover photo
        cover_photo = request.FILES.get('cover_photo')
        if cover_photo:
            cover_photo_path = os.path.join('cover_images', cover_photo.name)
            with open(os.path.join(settings.MEDIA_ROOT, cover_photo_path), 'wb+') as destination:
                for chunk in cover_photo.chunks():
                    destination.write(chunk)
            profile_data['cover_photo'] = cover_photo_path
        else:
            profile_data['cover_photo'] = profile['cover_photo']

        profile_update_query = """
            UPDATE profiles
            SET bio=%s, facebook=%s, twitter=%s, linkedIn=%s, github=%s,
                profile_picture=%s, cover_photo=%s
            WHERE user_id=%s AND user_type='student'
        """
        profile_params = [
            profile_data['bio'], profile_data['facebook'], profile_data['twitter'],
            profile_data['linkedIn'], profile_data['github'], profile_data['profile_picture'],
            profile_data['cover_photo'], student_id
        ]

        execute_query(profile_update_query, profile_params)

        # Overwrite PDF certificate if it exists
        courses_query = """
            SELECT course_id FROM certificates WHERE student_id = %s
        """
        courses = execute_query(courses_query, [student_id], fetchall=True)

        for course in courses:
            course_id = course['course_id']
            certificate_filename = f"certificate_{student_id}_{course_id}.pdf"
            certificate_path = os.path.join(settings.MEDIA_ROOT, certificate_filename)
            generate_certificate_pdf(certificate_path, student_id, course_id)

        # Return success response
        return JsonResponse({'success': True, 'message': 'Student profile updated successfully!'})

    # Fetch enrolled courses
    enrolled_courses_query = """
        SELECT c.name AS course_name, cat.name AS category_name
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN categories cat ON c.category_id = cat.id
        WHERE e.student_id = %s
    """
    enrolled_courses = execute_query(enrolled_courses_query, [student_id], fetchall=True)

    # Prepare specific URLs for the current student
    current_student_profile_picture_url = os.path.join(settings.MEDIA_URL, profile['profile_picture']).replace('\\', '/') if profile and profile.get('profile_picture') else None
    current_student_cover_photo_url = os.path.join(settings.MEDIA_URL, profile['cover_photo']).replace('\\', '/') if profile and profile.get('cover_photo') else None

    return render(request, 'account_app/admin_student_update.html', {
        'student': student,
        'profile': profile,
        'enrolled_courses': enrolled_courses,
        'current_student_profile_picture_url': current_student_profile_picture_url,
        'current_student_cover_photo_url': current_student_cover_photo_url
    })

# 4.6) Update Instructor and Profile by Admin
def update_instructor_profile(request, instructor_id):
    # Fetch instructor data
    instructor_query = "SELECT * FROM instructors WHERE id = %s"
    instructor = execute_query(instructor_query, [instructor_id], fetchone=True)

    if instructor['date_of_birth']:
        instructor['date_of_birth'] = instructor['date_of_birth'].strftime('%Y-%m-%d')

    # Ensure the instructor exists
    if not instructor:
        return JsonResponse({'success': False, 'error': 'Instructor not found.'})

    # Fetch or create the instructor's profile
    profile_query = "SELECT * FROM profiles WHERE user_id = %s AND user_type = 'instructor'"
    profile = execute_query(profile_query, [instructor_id], fetchone=True)

    # If profile does not exist, create it with default values
    if not profile:
        create_profile_query = """
            INSERT INTO profiles (bio, facebook, twitter, linkedIn, github, user_type, user_id, created_at)
            VALUES ('', '', '', '', '', 'instructor', %s, NOW())
        """
        execute_query(create_profile_query, [instructor_id])
        profile = execute_query(profile_query, [instructor_id], fetchone=True)

    if request.method == 'POST':
        data = request.POST
        errors = []

        # Validate form data
        if not data.get('first_name', '').strip():
            errors.append({'field': 'first_name', 'message': 'First name is required.'})
        if not data.get('last_name', '').strip():
            errors.append({'field': 'last_name', 'message': 'Last name is required.'})
        if not data.get('email_address', '').strip():
            errors.append({'field': 'email_address', 'message': 'Email address is required.'})
        if not data.get('phone_number', '').strip():
            errors.append({'field': 'phone_number', 'message': 'Phone number is required.'})

        # Validate email uniqueness
        if data['email_address'] and data['email_address'] != instructor['email_address']:
            query = "SELECT * FROM instructors WHERE email_address = %s"
            existing_instructor = execute_query(query, [data['email_address']], fetchone=True)
            if existing_instructor:
                errors.append({'field': 'email_address', 'message': 'Email address already exists.'})

        # Validate date of birth
        if data.get('date_of_birth'):
            try:
                dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
                age = (datetime.now() - dob).days // 365
                if age < 18:
                    errors.append({'field': 'date_of_birth', 'message': 'Instructor must be at least 18 years old.'})
            except ValueError:
                errors.append({'field': 'date_of_birth', 'message': 'Invalid date of birth format.'})

        # Handle errors
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Update instructor details
        instructor_update_query = """
            UPDATE instructors
            SET first_name=%s, middle_name=%s, last_name=%s, date_of_birth=%s, phone_number=%s,
                address=%s, department=%s, email_address=%s
            WHERE id=%s
        """
        instructor_params = [
            data.get('first_name', instructor['first_name']),
            data.get('middle_name', instructor['middle_name']),
            data.get('last_name', instructor['last_name']),
            data.get('date_of_birth', instructor['date_of_birth']),
            data.get('phone_number', instructor['phone_number']),
            data.get('address', instructor['address']),
            data.get('department', instructor['department']),
            data.get('email_address', instructor['email_address']),
            instructor_id
        ]

        execute_query(instructor_update_query, instructor_params)

        # Update profile details
        profile_data = {
            'bio': data.get('bio', profile['bio']),
            'facebook': data.get('facebook', profile['facebook']),
            'twitter': data.get('twitter', profile['twitter']),
            'linkedIn': data.get('linkedIn', profile['linkedIn']),
            'github': data.get('github', profile['github']),
            'user_id': instructor_id
        }

        # Check for new profile picture
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture:
            profile_picture_path = os.path.join('profile_images', profile_picture.name)
            with open(os.path.join(settings.MEDIA_ROOT, profile_picture_path), 'wb+') as destination:
                for chunk in profile_picture.chunks():
                    destination.write(chunk)
            profile_data['profile_picture'] = profile_picture_path
        else:
            profile_data['profile_picture'] = profile['profile_picture']

        # Check for new cover photo
        cover_photo = request.FILES.get('cover_photo')
        if cover_photo:
            cover_photo_path = os.path.join('cover_images', cover_photo.name)
            with open(os.path.join(settings.MEDIA_ROOT, cover_photo_path), 'wb+') as destination:
                for chunk in cover_photo.chunks():
                    destination.write(chunk)
            profile_data['cover_photo'] = cover_photo_path
        else:
            profile_data['cover_photo'] = profile['cover_photo']

        profile_update_query = """
            UPDATE profiles
            SET bio=%s, facebook=%s, twitter=%s, linkedIn=%s, github=%s,
                profile_picture=%s, cover_photo=%s
            WHERE user_id=%s AND user_type='instructor'
        """
        profile_params = [
            profile_data['bio'], profile_data['facebook'], profile_data['twitter'],
            profile_data['linkedIn'], profile_data['github'], profile_data['profile_picture'],
            profile_data['cover_photo'], instructor_id
        ]

        execute_query(profile_update_query, profile_params)

        # Return success response
        return JsonResponse({'success': True})

    # Prepare specific URLs for the current instructor
    current_instructor_profile_picture_url = os.path.join(settings.MEDIA_URL, profile['profile_picture']).replace('\\', '/') if profile and profile.get('profile_picture') else None
    current_instructor_cover_photo_url = os.path.join(settings.MEDIA_URL, profile['cover_photo']).replace('\\', '/') if profile and profile.get('cover_photo') else None

    return render(request, 'account_app/admin_instructor_update.html', {
        'instructor': instructor,
        'profile': profile,
        'current_instructor_profile_picture_url': current_instructor_profile_picture_url,
        'current_instructor_cover_photo_url': current_instructor_cover_photo_url
    })


# 4.7) update admin profile
def update_admin_profile(request, admin_id):
    # Fetch admin data for the specific admin being updated
    admin_query = "SELECT * FROM admins WHERE id = %s"
    admin = execute_query(admin_query, [admin_id], fetchone=True)

    if admin['date_of_birth']:
        admin['date_of_birth'] = admin['date_of_birth'].strftime('%Y-%m-%d')

    # Ensure the admin exists
    if not admin:
        return JsonResponse({'success': False, 'error': 'Admin not found.'})

    # Fetch or create the admin's profile
    profile_query = "SELECT * FROM profiles WHERE user_id = %s AND user_type = 'admin'"
    profile = execute_query(profile_query, [admin_id], fetchone=True)

    # If profile does not exist, create it with default values
    if not profile:
        create_profile_query = """
            INSERT INTO profiles (bio, facebook, twitter, linkedIn, github, user_type, user_id, created_at)
            VALUES ('', '', '', '', '', 'admin', %s, NOW())
        """
        execute_query(create_profile_query, [admin_id])
        profile = execute_query(profile_query, [admin_id], fetchone=True)

    if request.method == 'POST':
        data = request.POST
        errors = []

        # Validate input data
        if not data.get('first_name'):
            errors.append({'field': 'first_name', 'message': 'First name is required.'})
        if not data.get('middle_name'):
            errors.append({'field': 'middle_name', 'message': 'Middle name is required.'})
        if not data.get('last_name'):
            errors.append({'field': 'last_name', 'message': 'Last name is required.'})
        if not data.get('phone_number'):
            errors.append({'field': 'phone_number', 'message': 'Phone number is required.'})
        if not data.get('address'):
            errors.append({'field': 'address', 'message': 'Address is required.'})
        if not data.get('email_address'):
            errors.append({'field': 'email_address', 'message': 'Email address is required.'})

        # Validate age
        if data.get('date_of_birth'):
            try:
                dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                age = (timezone.now().date() - dob).days // 365
                if age < 18:
                    errors.append({'field': 'date_of_birth', 'message': 'Admin must be at least 18 years old.'})
            except ValueError:
                errors.append({'field': 'date_of_birth', 'message': 'Invalid date of birth format.'})

        # Handle file paths and uploads
        profile_data = {
            'bio': data.get('bio', profile.get('bio', '')),
            'facebook': data.get('facebook', profile.get('facebook', '')),
            'twitter': data.get('twitter', profile.get('twitter', '')),
            'linkedIn': data.get('linkedIn', profile.get('linkedIn', '')),
            'github': data.get('github', profile.get('github', '')),
        }

        # Check for new profile picture
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture:
            profile_picture_path = os.path.join('admin_profile_images', f"{admin_id}_{profile_picture.name}")
            profile_picture_full_path = os.path.join(settings.MEDIA_ROOT, profile_picture_path)
            os.makedirs(os.path.dirname(profile_picture_full_path), exist_ok=True)
            with open(profile_picture_full_path, 'wb+') as destination:
                for chunk in profile_picture.chunks():
                    destination.write(chunk)
            profile_data['profile_picture'] = profile_picture_path
        else:
            profile_data['profile_picture'] = profile.get('profile_picture', '')

        # Check for new cover photo
        cover_photo = request.FILES.get('cover_photo')
        if cover_photo:
            cover_photo_path = os.path.join('admin_cover_images', f"{admin_id}_{cover_photo.name}")
            cover_photo_full_path = os.path.join(settings.MEDIA_ROOT, cover_photo_path)
            os.makedirs(os.path.dirname(cover_photo_full_path), exist_ok=True)
            with open(cover_photo_full_path, 'wb+') as destination:
                for chunk in cover_photo.chunks():
                    destination.write(chunk)
            profile_data['cover_photo'] = cover_photo_path
        else:
            profile_data['cover_photo'] = profile.get('cover_photo', '')

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Update admin details in the database
        admin_update_query = """
            UPDATE admins
            SET first_name=%s, middle_name=%s, last_name=%s, date_of_birth=%s, phone_number=%s,
                address=%s, email_address=%s
            WHERE id=%s
        """
        admin_params = [
            data.get('first_name', admin['first_name']),
            data.get('middle_name', admin['middle_name']),
            data.get('last_name', admin['last_name']),
            data.get('date_of_birth', admin['date_of_birth']),
            data.get('phone_number', admin['phone_number']),
            data.get('address', admin['address']),
            data.get('email_address', admin['email_address']),
            admin_id
        ]

        execute_query(admin_update_query, admin_params)

        # Update profile details in the database
        profile_update_query = """
            UPDATE profiles
            SET bio=%s, facebook=%s, twitter=%s, linkedIn=%s, github=%s,
                profile_picture=%s, cover_photo=%s
            WHERE user_id=%s AND user_type='admin'
        """
        profile_params = [
            profile_data['bio'], profile_data['facebook'], profile_data['twitter'],
            profile_data['linkedIn'], profile_data['github'], profile_data['profile_picture'],
            profile_data['cover_photo'], admin_id
        ]

        execute_query(profile_update_query, profile_params)

        return JsonResponse({'success': True, 'message': 'Admin profile updated successfully!'})

    # Construct URLs for profile picture and cover photo for the specific admin being updated
    current_admin_profile_picture_url = os.path.join(settings.MEDIA_URL, profile.get('profile_picture', '')).replace('\\', '/') if profile and profile.get('profile_picture') else None
    current_admin_cover_photo_url = os.path.join(settings.MEDIA_URL, profile.get('cover_photo', '')).replace('\\', '/') if profile and profile.get('cover_photo') else None

    return render(request, 'account_app/admin_update_and_profile.html', {
        'admin': admin,
        'profile': profile,
        'current_admin_profile_picture_url': current_admin_profile_picture_url,
        'current_admin_cover_photo_url': current_admin_cover_photo_url
    })


# -----------------------------------------------------> End: Student Profile Management <-----------------------------------------------------