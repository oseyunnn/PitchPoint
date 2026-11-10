from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

UserAccount = get_user_model()

def register_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email")
        role = request.POST.get("role") or "student"
        position = request.POST.get("position", "")
        pass1 = request.POST.get("pass1")
        pass2 = request.POST.get("pass2")

        if not username:
            messages.error(request, "Please choose a username.")
            return render(request, "register/register.html")

        if UserAccount.objects.filter(username__iexact=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, "register/register.html")

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
            username=username,
            role=role,
            position=position
        )
        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login:login")

    return render(request, "register/register.html")