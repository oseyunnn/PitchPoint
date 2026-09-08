from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages 
from .models import UserProfile

def register_view(request):
    if request.method == "POST":
        fname = request.POST.get('fullname')
        uname = request.POST.get('username')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if not fname or not uname or not pass1 or not pass2:
            messages.error(request, "All fields are required!")
            return redirect('register')

        if pass1 != pass2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')

        user = User.objects.create_user(username=uname, password=pass1)
        UserProfile.objects.create(user=user, full_name=fname)
        
        messages.success(request, "Registration successful! Please login.")
        return redirect('login')
        
    return render(request, 'register/register.html')