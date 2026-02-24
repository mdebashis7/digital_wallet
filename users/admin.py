from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "is_active", "is_staff")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)
    search_fields = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )



from .models import TransactionPin

@admin.register(TransactionPin)
class TransactionPinAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
