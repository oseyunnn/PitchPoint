from django.urls import path
from .views import login_screen

app_name = "login"  
urlpatterns = [
    path("", login_screen, name="login"),
]