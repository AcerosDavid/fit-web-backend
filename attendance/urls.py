from django.urls import path
from .views import AttendanceListView, CheckInView, CheckOutView, ScanQrView

urlpatterns = [
    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/check-in/', CheckInView.as_view(), name='attendance-check-in'),
    path('attendance/scan/', ScanQrView.as_view(), name='attendance-scan'),
    path('attendance/<int:pk>/check-out/', CheckOutView.as_view(), name='attendance-check-out'),
]
