from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')

def login_view(request):
    return render(request, 'login.html')

def register_view(request):
    return render(request, 'register.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')

def load_view(request, view_name):
    if view_name == "desks":
        return render(request, "partials/desks.html")
    elif view_name == "overview":
        return render(request, "partials/overview.html")
    else:
        return render(request, "partials/desks.html")
def overview(request):
    return render(request, "partials/overview.html")

def desk(request):
    return render(request, "partials/desks.html")
