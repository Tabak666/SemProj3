from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/',views.dashboard_view, name='dashboard'),
    path('load_view/<str:view_name>/', views.load_view, name='load_view'),
    path("", views.overview, name="overview"),
    path("desk/", views.desk, name="desk_view"),
]
