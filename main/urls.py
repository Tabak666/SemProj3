from django.urls import path
from .views import (
    index, login_view, register_view, dashboard_view, load_view, overview,
    desk, logout_view, approvals_view, forgot_password_view,
    pair_desk_view, unpair_desk_view, user_desk_status,
    desks_status_api, set_desk_height, book_desk_view
)

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('load_view/<str:view_name>/', load_view, name='load_view'),
    path('overview/', overview, name="overview"),
    path("desk/", desk, name="desk_view"),
    path('logout/', logout_view, name='logout'),
    path('approvals/', approvals_view, name='approvals'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('pair_desk/', pair_desk_view, name='pair_desk'),
    path('unpair_desk/', unpair_desk_view, name='unpair_desk'),
    path("api/user-status/<str:desk_id>/", user_desk_status, name="user_desk_status"),
    path("api/desks_status/", desks_status_api, name="desks_status_api"),
    path('api/set_desk_height/', set_desk_height, name='set_desk_height'),
    path('desk/book/', book_desk_view, name='book_desk'),
]
