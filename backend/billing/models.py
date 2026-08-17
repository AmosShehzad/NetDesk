from django.db import models
from django.conf import settings


class Bill(models.Model):
    class Status(models.TextChoices):
        PAID = 'PAID', 'Paid'
        UNPAID = 'UNPAID', 'Unpaid'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bills', limit_choices_to={'role': 'CUSTOMER'}
    )
    month = models.CharField(max_length=20)  # e.g. "August 2026"
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.reg_number} — {self.month} ({self.status})"