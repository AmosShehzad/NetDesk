from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User


@receiver(pre_save, sender=User)
def generate_reg_number(sender, instance, **kwargs):
    if not instance.reg_number:
        year = timezone.now().year
        prefix = 'STAFF' if instance.role != 'CUSTOMER' else 'CUST'
        count = User.objects.filter(reg_number__startswith=f"{prefix}-{year}").count() + 1
        instance.reg_number = f"{prefix}-{year}-{count:05d}"