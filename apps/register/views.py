from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

UserAccount = get_user_model()

def register_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        name = request.POST.get("name")
        role = request.POST.get("role", "student")
        
        if UserAccount.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "register/register.html")

        user = UserAccount.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=role
        )
        return redirect("login:login")

    return render(request, "register/register.html")