from django.urls import path
from . import views

aop_name = "register"
urlpatterns = [
    path('', views.register_view, name='register'),
]