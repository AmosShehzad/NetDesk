from django.contrib import admin
from .models import Ticket, TicketCategory, TicketComment, InternalNote, Attachment


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    fields = ['author', 'message', 'created_at']
    readonly_fields = ['created_at']


class InternalNoteInline(admin.TabularInline):
    model = InternalNote
    extra = 0
    fields = ['author', 'message', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'title', 'status', 'priority', 'customer', 'escalated', 'ai_reply_count', 'created_at']
    list_filter = ['status', 'priority', 'category', 'escalated']
    search_fields = ['ticket_number', 'title']
    inlines = [TicketCommentInline, InternalNoteInline]


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'created_at']


@admin.register(InternalNote)
class InternalNoteAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'created_at']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'uploaded_by', 'file', 'uploaded_at']
