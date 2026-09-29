from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages 
from .models import UserProfile

def register_view(request):
    if request.method == "POST":
        fname = request.POST.get('fullname')
        uname = request.POST.get('username')
        position = request.POST.get('position')
        email = request.POST.get('ttsp_email')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if not fname or not uname or not position or not email or not pass1 or not pass2:
            messages.error(request, "All fields are required!")
            return redirect('register:register')

        if pass1 != pass2:
            messages.error(request, "Passwords do not match!")
            return redirect('register:register')

        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username already taken!")
            return redirect('register:register')

        user = User.objects.create_user(username=uname, password=pass1, email=email)
        UserProfile.objects.create(
            user=user, 
            full_name=fname,
            position=position,
            ttsp_email=email
        )
        
        messages.success(request, "Registration successful! Please login.")
        return redirect('login:login')
        
    return render(request, 'register/register.html')