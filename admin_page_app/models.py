# admin_page_app/models.py

from django.db import models
from account_app.models import Student, Instructor
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)  # Added image field
    level = models.CharField(max_length=50, default='Beginner')
    language = models.CharField(max_length=50, default='English')
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categories'

class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)  # Added image field
    course_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Add course amount field
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'courses'

class Payment(models.Model):
    expected_course_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    sender_phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=(('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')), default='pending')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.course.name} by {self.student.first_name}"
    
    class Meta:
        db_table = 'payments'


class Enrollment(models.Model):
    enrollment_date = models.DateField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.email_address} enrolled in {self.course.name}"

    class Meta:
        db_table = 'enrollments'

class Certificate(models.Model):
    issue_date = models.DateField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate for {self.student.email_address} in {self.course.name}"

    class Meta:
        db_table = 'certificates'

class Review(models.Model):
    review_text = models.TextField()
    rating = models.IntegerField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.student.email_address} for {self.course.name}"

    class Meta:
        db_table = 'reviews'

class Lesson(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    video_url = models.TextField(blank=True, null=True)  # Changed to TextField to accommodate full embed code
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    duration = models.DecimalField(max_digits=5, decimal_places=2, help_text='Duration in hours', default=0.00)
    order = models.IntegerField(default=0)  # Add this field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'lessons'

class LessonCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completion_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.email_address} completed {self.lesson.title}"

    class Meta:
        db_table = 'lesson_completions'
        unique_together = ('student', 'lesson')


class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    video_url = models.TextField(blank=True, null=True)  # Optional field for video embed code
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question
    
    class Meta:
        db_table = 'faqs'


class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    event_date = models.DateField()
    event_time = models.TimeField()  # New field for event time
    event_place = models.CharField(max_length=255)  # New field for event place
    event_status = models.CharField(max_length=50)  # New field for event status (e.g., "Upcoming", "Completed")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # Foreign key to Course
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'events'








class Zoom(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    zoom_event_date = models.DateField()
    zoom_link = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'zooms'


class Assignment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateField()
    max_score = models.IntegerField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'assignments'

class AssignmentSubmission(models.Model):
    submission_file = models.CharField(max_length=255)
    submission_date = models.DateTimeField()
    score = models.IntegerField()
    feedback = models.TextField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.student.email_address} for {self.assignment.name}"

    class Meta:
        db_table = 'assignment_submissions'

class Quiz(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    max_score = models.IntegerField()
    duration = models.IntegerField()  # Duration in minutes
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'quizzes'

class QuizQuestion(models.Model):
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=(('multiple_choice', 'Multiple Choice'), ('true_false', 'True/False')))
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'quiz_questions'

class QuizAnswer(models.Model):
    answer_text = models.TextField()
    is_correct = models.BooleanField()
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.answer_text

    class Meta:
        db_table = 'quiz_answers'

class StudentQuizSubmission(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    total_score = models.IntegerField()
    selected_answer = models.ForeignKey(QuizAnswer, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.student.email_address} for {self.quiz.name}"

    class Meta:
        db_table = 'student_quiz_submissions'

