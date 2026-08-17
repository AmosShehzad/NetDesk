from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    TicketViewSet, TicketCategoryViewSet,
    TicketCommentViewSet, InternalNoteViewSet, AttachmentViewSet,
    DashboardView,
)

router = DefaultRouter()
router.register('tickets', TicketViewSet, basename='ticket')
router.register('categories', TicketCategoryViewSet, basename='category')
router.register('comments', TicketCommentViewSet, basename='comment')
router.register('internal-notes', InternalNoteViewSet, basename='internal-note')
router.register('attachments', AttachmentViewSet, basename='attachment')

urlpatterns = router.urls + [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]