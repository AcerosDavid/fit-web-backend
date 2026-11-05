from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, status, views
from rest_framework.response import Response
from django.utils import timezone

from coaches.models import Coach, CoachAttendance
from coaches.serializers import CoachAttendanceSerializer, CoachSerializer
from config.serializers import ErrorMessageSerializer
from .models import Attendance
from members.models import Member
from members.serializers import MemberSerializer
from .serializers import (
    AttendanceSerializer,
    CheckInSerializer,
    ScanRequestSerializer,
    ScanResultSerializer,
)
from members.views import IsAdminOrReceptionist

MEMBER_QR_PREFIX = 'FIT-M-'
COACH_QR_PREFIX = 'FIT-C-'


def _resolve_qr_code(raw_code):
    """Devuelve (tipo, id) a partir del código QR, o (None, None)."""
    code = (raw_code or '').strip().upper()

    for prefix, kind in ((MEMBER_QR_PREFIX, 'member'), (COACH_QR_PREFIX, 'coach')):
        if code.startswith(prefix):
            value = code[len(prefix):]
            if value.isdigit():
                return kind, int(value)
            return None, None
    return None, None

@extend_schema(
    tags=['attendance'],
    summary='Listar asistencias',
    description='Historial de check-in/check-out, filtrable por cliente y fecha.',
    parameters=[
        OpenApiParameter(
            name='member', type=OpenApiTypes.INT, required=False,
            description='Filtra por ID de cliente',
        ),
        OpenApiParameter(
            name='date', type=OpenApiTypes.DATE, required=False,
            description='Filtra por fecha de check-in (YYYY-MM-DD)',
        ),
    ],
)
class AttendanceListView(generics.ListAPIView):
    """
    GET /api/attendance/ -> List all attendances
    """
    queryset = Attendance.objects.select_related('member')
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

@extend_schema(
    tags=['attendance'],
    summary='Registrar check-in',
    description=(
        'Registra la entrada de un cliente al gimnasio. Devuelve 404 si el '
        'cliente no existe o está inactivo, y 400 si ya tiene una asistencia '
        'abierta (incluye attendance_id).'
    ),
    request=CheckInSerializer,
    responses={
        201: AttendanceSerializer,
        400: ErrorMessageSerializer,
        404: ErrorMessageSerializer,
    },
)
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

@extend_schema(
    tags=['attendance'],
    summary='Registrar check-out',
    description='Cierra la asistencia activa del cliente. Devuelve 404 si no hay asistencia abierta.',
    request=None,  # POST sin cuerpo
    responses={200: AttendanceSerializer, 404: ErrorMessageSerializer},
)
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


@extend_schema(
    tags=['attendance'],
    summary='Escanear QR y registrar asistencia',
    description=(
        'Identifica a un cliente o entrenador por su código QR '
        '(`FIT-M-<id>` o `FIT-C-<id>`) y registra automáticamente la entrada '
        'si no tiene una asistencia abierta, o la salida si ya está dentro.'
    ),
    request=ScanRequestSerializer,
    responses={
        200: ScanResultSerializer,
        400: ErrorMessageSerializer,
        404: ErrorMessageSerializer,
    },
)
class ScanQrView(views.APIView):
    """
    POST /api/attendance/scan/
    Body: { "code": "FIT-M-1" } o { "code": "FIT-C-3" }
    """
    permission_classes = [IsAdminOrReceptionist]

    def post(self, request):
        serializer = ScanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        kind, entity_id = _resolve_qr_code(serializer.validated_data['code'])
        if kind is None:
            return Response(
                {'error': 'Invalid QR code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if kind == 'member':
            return self._scan_member(request, entity_id)
        return self._scan_coach(request, entity_id)

    def _scan_member(self, request, member_id):
        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            return Response(
                {'error': 'Member not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if member.status != Member.Status.ACTIVE:
            return Response(
                {'error': 'Member is not active.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_attendance = Attendance.objects.filter(
            member=member, check_out__isnull=True,
        ).first()

        if active_attendance:
            active_attendance.check_out = timezone.now()
            active_attendance.save(update_fields=['check_out'])
            attendance = active_attendance
            action = 'check-out'
        else:
            attendance = Attendance.objects.create(
                member=member,
                check_in=timezone.now(),
                registered_by=request.user,
            )
            action = 'check-in'

        message = (
            f"Salida registrada: {member.full_name}"
            if action == 'check-out'
            else f"Entrada registrada: {member.full_name}"
        )

        return Response({
            'type': 'member',
            'action': action,
            'qr_code': member.qr_code,
            'person': MemberSerializer(member).data,
            'attendance': AttendanceSerializer(attendance).data,
            'message': message,
        })

    def _scan_coach(self, request, coach_id):
        try:
            coach = Coach.objects.get(pk=coach_id)
        except Coach.DoesNotExist:
            return Response(
                {'error': 'Coach not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not coach.is_active:
            return Response(
                {'error': 'Coach is not active.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_attendance = CoachAttendance.objects.filter(
            coach=coach, check_out__isnull=True,
        ).first()

        if active_attendance:
            active_attendance.check_out = timezone.now()
            active_attendance.save(update_fields=['check_out'])
            attendance = active_attendance
            action = 'check-out'
        else:
            attendance = CoachAttendance.objects.create(
                coach=coach,
                check_in=timezone.now(),
                registered_by=request.user,
            )
            action = 'check-in'

        message = (
            f"Salida registrada: {coach.full_name}"
            if action == 'check-out'
            else f"Entrada registrada: {coach.full_name}"
        )

        return Response({
            'type': 'coach',
            'action': action,
            'qr_code': coach.qr_code,
            'person': CoachSerializer(coach).data,
            'attendance': CoachAttendanceSerializer(attendance).data,
            'message': message,
        })
