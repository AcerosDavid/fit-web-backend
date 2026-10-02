from django.urls import path
from .views import MembershipListCreateView, MembershipDetailView

urlpatterns = [
    path('memberships/', MembershipListCreateView.as_view(), name='membership-list'),
    path('memberships/<int:pk>/', MembershipDetailView.as_view(), name='membership-detail'),
]
