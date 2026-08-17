from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone_number', 'username', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].initial = '12345678'
        self.fields['password2'].initial = '12345678'
        self.fields['password1'].help_text = "Default: 12345678 — customer will be forced to change this on first login."


class CustomUserAdmin(UserAdmin):
    model = User
    add_form = CustomUserCreationForm
    list_display = ['reg_number', 'phone_number', 'username', 'role', 'is_staff']
    list_filter = ['role']
    ordering = ['reg_number']
    fieldsets = UserAdmin.fieldsets + (('Role Info', {'fields': ('role', 'phone_number')}),)
    add_fieldsets = (
        (None, {'fields': ('phone_number', 'username', 'role', 'password1', 'password2')}),
    )


admin.site.register(User, CustomUserAdmin)