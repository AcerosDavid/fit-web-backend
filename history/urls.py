from django.urls import path

from .views import GlobalHistoryView, MemberHistoryView

urlpatterns = [
    path(
        'members/<int:pk>/history/',
        MemberHistoryView.as_view(),
        name='member-history',
    ),
    path('history/', GlobalHistoryView.as_view(), name='global-history'),
]
