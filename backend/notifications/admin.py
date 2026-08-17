from django.contrib import admin
from .models import Notification

from .models import Notification, Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['message', 'created_at']
    
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message', 'ticket', 'is_read', 'created_at']
    list_filter = ['is_read']