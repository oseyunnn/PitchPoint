from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("home:index")
        else:
            messages.error(request, "Invalid email or password.")
            
    return render(request, "login/login.html")