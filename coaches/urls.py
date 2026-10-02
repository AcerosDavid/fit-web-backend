from django.urls import path
from .views import CoachListCreateView, CoachDetailView

urlpatterns = [
    path('coaches/', CoachListCreateView.as_view(), name='coach-list'),
    path('coaches/<int:pk>/', CoachDetailView.as_view(), name='coach-detail'),
]
