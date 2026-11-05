from django.urls import path

from .views import (
    CoachCheckInView,
    CoachCheckOutView,
    CoachDetailView,
    CoachHistoryView,
    CoachListCreateView,
)

urlpatterns = [
    path('coaches/', CoachListCreateView.as_view(), name='coach-list'),
    path('coaches/<int:pk>/', CoachDetailView.as_view(), name='coach-detail'),
    path(
        'coaches/<int:pk>/history/',
        CoachHistoryView.as_view(),
        name='coach-history',
    ),
    path(
        'coaches/<int:pk>/check-in/',
        CoachCheckInView.as_view(),
        name='coach-check-in',
    ),
    path(
        'coaches/<int:pk>/check-out/',
        CoachCheckOutView.as_view(),
        name='coach-check-out',
    ),
]
