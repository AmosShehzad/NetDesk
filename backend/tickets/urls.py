from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    TicketViewSet, TicketCategoryViewSet,
    TicketCommentViewSet, InternalNoteViewSet, AttachmentViewSet,
    TicketRatingViewSet, TicketActivityViewSet, OutageViewSet,
    DashboardView,
)

router = DefaultRouter()
router.register('tickets', TicketViewSet, basename='ticket')
router.register('categories', TicketCategoryViewSet, basename='category')
router.register('comments', TicketCommentViewSet, basename='comment')
router.register('internal-notes', InternalNoteViewSet, basename='internal-note')
router.register('attachments', AttachmentViewSet, basename='attachment')
router.register('ratings', TicketRatingViewSet, basename='rating')
router.register('activities', TicketActivityViewSet, basename='activity')
router.register('outages', OutageViewSet, basename='outage')

urlpatterns = router.urls + [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]