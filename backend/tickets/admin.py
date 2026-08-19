from django.contrib import admin
from .models import (
    Ticket, TicketCategory, TicketComment, InternalNote,
    Attachment, TicketRating, TicketActivity, Outage,
)


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


class TicketActivityInline(admin.TabularInline):
    model = TicketActivity
    extra = 0
    fields = ['actor', 'action', 'details', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'title', 'status', 'priority', 'customer',
                    'escalated', 'ai_reply_count', 'sla_deadline', 'created_at']
    list_filter = ['status', 'priority', 'category', 'escalated']
    search_fields = ['ticket_number', 'title']
    readonly_fields = ['sla_deadline', 'resolved_at', 'closed_at']
    inlines = [TicketCommentInline, InternalNoteInline, TicketActivityInline]


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


@admin.register(TicketRating)
class TicketRatingAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'score', 'created_at']
    list_filter = ['score']


@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'actor', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['ticket__ticket_number', 'action']


@admin.register(Outage)
class OutageAdmin(admin.ModelAdmin):
    list_display = ['area', 'status', 'started_at', 'resolved_at', 'created_by']
    list_filter = ['status', 'area']
    search_fields = ['area', 'description']