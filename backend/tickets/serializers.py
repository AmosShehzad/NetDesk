from rest_framework import serializers
from .models import Ticket, TicketCategory, TicketComment, InternalNote, Attachment


class TicketCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = TicketComment
        fields = ['id', 'ticket', 'author', 'author_username', 'message', 'created_at']
        read_only_fields = ['author']


class InternalNoteSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = InternalNote
        fields = ['id', 'ticket', 'author', 'author_username', 'message', 'created_at']
        read_only_fields = ['author']


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'ticket', 'uploaded_by', 'uploaded_by_username', 'file', 'download_url', 'uploaded_at']
        read_only_fields = ['uploaded_by']

    def get_download_url(self, obj):
        # Points to the SECURED endpoint, not a raw media path
        return f"/api/attachments/{obj.id}/download/"

    def validate_file(self, value):
        max_size_mb = 10
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File too large. Max size is {max_size_mb}MB.")
        ext = '.' + value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}"
            )
        return value


class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description']


class TicketSerializer(serializers.ModelSerializer):
    """
    Handles both reading and writing tickets.
    Some fields are read-only because customers should never set them directly
    (e.g. they can't assign their own agent or set priority to CRITICAL themselves
    — that decision belongs to staff).
    """
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    assigned_agent_username = serializers.CharField(
        source='assigned_agent.username', read_only=True, default=None
    )

    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'title', 'description',
            'category', 'status', 'priority',
            'customer', 'customer_username',
            'assigned_agent', 'assigned_agent_username',
            'assigned_technician',
            'created_at', 'updated_at', 'closed_at',
        ]
        read_only_fields = [
            'ticket_number', 'status', 'customer',
            'assigned_agent', 'assigned_technician', 'closed_at',
        ]