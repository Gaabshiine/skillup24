from django.shortcuts import render

# Create your views here.


def dashboard(request):
    return render(request, 'admin_page_app/admin_dashboard.html')
