from django.contrib.auth.models import BaseUserManager
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email


from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta

class TransactionPin(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="transaction_pin"
    )

    pin_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    def set_pin(self, raw_pin):
        self.pin_hash = make_password(raw_pin)

    def verify_pin(self, raw_pin):
        return check_password(raw_pin, self.pin_hash)

    def __str__(self):
        return f"Transaction PIN for {self.user.email}"  
    

    def is_locked(self):
        return self.locked_until and timezone.now() < self.locked_until


    def register_failure(self):
        self.failed_attempts += 1

        if self.failed_attempts >= 3:
            self.locked_until = timezone.now() + timedelta(minutes=10)

        self.save(update_fields=["failed_attempts", "locked_until"])


    def reset_failures(self):
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=["failed_attempts", "locked_until"])



    
