from rest_framework import viewsets, permissions
from .models import Bill
from .serializers import BillSerializer


class BillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only — bills are created/managed by staff in Django Admin only.
    Customer sees only their own bills; staff sees all.
    """
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'CUSTOMER':
            return Bill.objects.filter(customer=user)
        return Bill.objects.all()