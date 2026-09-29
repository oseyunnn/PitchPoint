from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

UserAccount = get_user_model()

def register_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        role = request.POST.get("role")
        position = request.POST.get("position", "")
        pass1 = request.POST.get("pass1")
        pass2 = request.POST.get("pass2")

        if pass1 != pass2:
            messages.error(request, "Passwords do not match.")
            return render(request, "register/register.html")

        if UserAccount.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "register/register.html")

        # Create user with UserAccount custom manager
        user = UserAccount.objects.create_user(
            email=email,
            password=pass1,
            name=name,
            role=role,
            position=position
        )
        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login:login")

    return render(request, "register/register.html")