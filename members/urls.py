from django.urls import path
from .views import MemberListCreateView, MemberDetailView, MemberDeleteView, MemberRestoreView

urlpatterns = [
    path("members/",                      MemberListCreateView.as_view(), name="member-list"),
    path("members/<int:pk>/",             MemberDetailView.as_view(),     name="member-detail"),
    path("members/<int:pk>/delete/",      MemberDeleteView.as_view(),     name="member-delete"),
    path("members/<int:pk>/restore/",     MemberRestoreView.as_view(),    name="member-restore"),
]
