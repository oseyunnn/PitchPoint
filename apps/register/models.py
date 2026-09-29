import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserAccountManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("account_status", "active")

        return self.create_user(
            email=email,
            password=password,
            **extra_fields
        )


class UserAccount(AbstractBaseUser):

    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=255
    )

    email = models.EmailField(
        unique=True
    )

    role = models.CharField(
        max_length=30
    )

    position = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    account_status = models.CharField(
        max_length=30,
        default="active"
    )

    student_id = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )

    course = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    year_level = models.SmallIntegerField(
        null=True,
        blank=True
    )

    contact_number = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    profile_picture_url = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    objects = UserAccountManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "name"
    ]

    def __str__(self):
        return self.email