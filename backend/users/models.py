from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, password=None, **extra_fields):
        # reg_number is intentionally left blank here — a signal auto-fills it on save
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        SUPPORT_AGENT = 'SUPPORT_AGENT', 'Support Agent'
        TECHNICIAN = 'TECHNICIAN', 'Technician'
        MANAGER = 'MANAGER', 'Manager'
        ADMIN = 'ADMIN', 'Admin'

    username = models.CharField(max_length=150, blank=True, null=True)
    reg_number = models.CharField(max_length=20, unique=True, blank=True)
    phone_regex = RegexValidator(regex=r'^\d{11}$', message="Phone must be exactly 11 digits.")
    phone_number = models.CharField(max_length=11, validators=[phone_regex], unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    must_change_password = models.BooleanField(default=True)

    USERNAME_FIELD = 'reg_number'
    REQUIRED_FIELDS = ['phone_number']

    objects = UserManager()

    def __str__(self):
        return f"{self.reg_number} ({self.role})"
    
class Customer(models.Model):
    """
    Extra profile data for users with role=CUSTOMER.
    One-to-One with User: each customer user has exactly one profile.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,     # if User is deleted, delete this profile too
        related_name='customer_profile',
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    service_area = models.CharField(max_length=100, blank=True)
    internet_package = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Customer: {self.user.username}"