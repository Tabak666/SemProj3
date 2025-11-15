from django.urls import path
from . import views

app_name = 'cleaningAPI'

urlpatterns = [
    path('hello', views.hello, name='hello'),
    path('clean', views.toggleCleaningMode, name='cleaning mode button')
]