
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
    path('logout/', views.logout_view, name='logout'),
    path('approvals/', views.approvals_view, name='approvals'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('pair_desk/', views.pair_desk_view, name='pair_desk'),
    path('unpair_desk/', views.unpair_desk_view, name='unpair_desk'),
]
