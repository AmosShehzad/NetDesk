from django.contrib import admin
from .models import Bill


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['customer', 'month', 'amount', 'status', 'due_date']
    list_filter = ['status', 'month']