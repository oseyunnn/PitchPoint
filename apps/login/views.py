from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_screen(request):
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')

        if not u or not p:
            messages.error(request, "Please enter both username and password.")
            return redirect('login')

        user = authenticate(username=u, password=p)

        if user is not None:
            login(request, user)
            return redirect('home:home')
        else:
            messages.error(request, "Invalid Username or Password.")
            return redirect('login')

    return render(request, 'login/login.html')