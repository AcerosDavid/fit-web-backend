from rest_framework import generics, status, views
from rest_framework.response import Response
from django.utils import timezone
from .models import Attendance
from members.models import Member
from .serializers import AttendanceSerializer, CheckInSerializer
from members.views import IsAdminOrReceptionist

class AttendanceListView(generics.ListAPIView):
    """
    GET /api/attendance/ -> List all attendances
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAdminOrReceptionist]

    def get_queryset(self):
        queryset = super().get_queryset()
        member_id = self.request.query_params.get('member')
        date_param = self.request.query_params.get('date') # e.g. YYYY-MM-DD
        
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        if date_param:
            queryset = queryset.filter(check_in__date=date_param)
            
        return queryset

class CheckInView(views.APIView):
    """
    POST /api/attendance/check-in/
    Body: { "member_id": 1 }
    """
    permission_classes = [IsAdminOrReceptionist]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        if serializer.is_valid():
            member_id = serializer.validated_data['member_id']
            
            try:
                member = Member.objects.get(id=member_id, status=Member.Status.ACTIVE)
            except Member.DoesNotExist:
                return Response({"error": "Member not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if already checked in and not checked out
            active_attendance = Attendance.objects.filter(
                member=member, 
                check_out__isnull=True
            ).first()
            
            if active_attendance:
                return Response({
                    "error": "Member is already checked in",
                    "attendance_id": active_attendance.id
                }, status=status.HTTP_400_BAD_REQUEST)
                
            attendance = Attendance.objects.create(
                member=member,
                check_in=timezone.now(),
                registered_by=request.user
            )
            
            return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckOutView(views.APIView):
    """
    POST /api/attendance/{id}/check-out/
    """
    permission_classes = [IsAdminOrReceptionist]

    def post(self, request, pk):
        try:
            attendance = Attendance.objects.get(pk=pk, check_out__isnull=True)
            attendance.check_out = timezone.now()
            attendance.save()
            return Response(AttendanceSerializer(attendance).data)
        except Attendance.DoesNotExist:
            return Response({"error": "Active attendance not found"}, status=status.HTTP_404_NOT_FOUND)
