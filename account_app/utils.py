from django.db import connection
from django.contrib.auth.hashers import make_password
from datetime import datetime
from django.utils.dateparse import parse_date




def execute_query(query, params=None, fetchone=False, fetchall=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        if fetchone:
            row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row)) if row else None
        if fetchall:
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        connection.commit()

def extract_user_data(request):
    errors = {}
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
    }

    # Validate required fields
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

    if not data['phone_number']:
        errors['phone_number'] = 'Phone number is required.'

    if not data['gender']:
        errors['gender'] = 'Gender is required.'

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

    if not data['address']:
        errors['address'] = 'Address is required.'

    if not data['major']:
        errors['major'] = 'Major is required.'

    # Validate email uniqueness
    if data['email_address']:
        query = "SELECT * FROM students WHERE email_address = %s"
        student = execute_query(query, [data['email_address']], fetchone=True)
        if student:
            errors['email_address'] = 'Email address already exists.'
    else:
        errors['email_address'] = 'Email address is required.'

    # Validate password
    if not data['password']:
        errors['password'] = 'Password is required.'
    elif len(data['password']) < 8:
        errors['password'] = 'Password must be at least 8 characters long.'

    # Validate confirm password
    if data['confirm_password'] != data['password']:
        errors['confirm_password'] = 'Passwords do not match.'

    return data, errors


def hash_password(password):
    return make_password(password)


def update_user_data(request):
    errors = {}
    data = {
        'first_name': request.POST.get('first_name', '').strip(),
        'middle_name': request.POST.get('middle_name', '').strip(),
        'last_name': request.POST.get('last_name', '').strip(),
        'phone_number': request.POST.get('phone_number', '').strip(),
        'gender': request.POST.get('gender', '').strip(),
        'date_of_birth': request.POST.get('date_of_birth', '').strip(),
        'address': request.POST.get('address', '').strip(),
        'major': request.POST.get('major_or_department', '').strip(),
        'bio': request.POST.get('bio', '').strip(),
        'facebook': request.POST.get('facebook', '').strip(),
        'twitter': request.POST.get('twitter', '').strip(),
        'linkedIn': request.POST.get('linkedIn', '').strip(),
        'github': request.POST.get('github', '').strip(),
    }

    # Validate required fields
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

    if not data['phone_number']:
        errors['phone_number'] = 'Phone number is required.'

    if not data['gender']:
        errors['gender'] = 'Gender is required.'

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

    if not data['address']:
        errors['address'] = 'Address is required.'

    if not data['major']:
        errors['major'] = 'Major is required.'

    return data, errors



