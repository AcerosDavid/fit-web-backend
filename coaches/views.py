from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import generics, status, views
from rest_framework.response import Response

from config.serializers import DetailMessageSerializer, ErrorMessageSerializer
from members.views import IsAdminOrReceptionist
from .models import Coach, CoachAttendance
from .serializers import (
    CoachAttendanceSerializer,
    CoachHistorySerializer,
    CoachSerializer,
)


def _parse_date_param(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return None, None
    try:
        parsed = parse_date(raw)
    except ValueError:
        parsed = None
    if parsed is None:
        return None, f"Invalid '{name}' format. Use YYYY-MM-DD."
    return parsed, None


def _parse_date_range(request):
    date_from, error = _parse_date_param(request, 'date_from')
    if error:
        return None, None, error
    date_to, error = _parse_date_param(request, 'date_to')
    if error:
        return None, None, error
    if date_from and date_to and date_from > date_to:
        return None, None, "'date_from' cannot be after 'date_to'."
    return date_from, date_to, None


@extend_schema(
    tags=['coaches'],
    summary='Listar o crear entrenadores',
    description='GET lista los entrenadores activos; POST crea uno.',
)
class CoachListCreateView(generics.ListCreateAPIView):
    """
    GET /api/coaches/ -> List all coaches
    POST /api/coaches/ -> Create a coach
    """
    queryset = Coach.objects.filter(is_active=True)
    serializer_class = CoachSerializer
    permission_classes = [IsAdminOrReceptionist]


@extend_schema(
    tags=['coaches'],
    summary='Detalle/actualizar/eliminar un entrenador',
    description='DELETE hace soft-delete (is_active=False) para conservar el historial.',
)
class CoachDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/coaches/{id}/ -> View coach details
    PUT/PATCH /api/coaches/{id}/ -> Edit coach
    DELETE /api/coaches/{id}/ -> Delete (soft/hard depending on logic)
    """
    queryset = Coach.objects.all()
    serializer_class = CoachSerializer
    permission_classes = [IsAdminOrReceptionist]

    def perform_destroy(self, instance):
        # Soft delete coach
        instance.is_active = False
        instance.save()


@extend_schema(
    tags=['coaches'],
    summary='Historial de asistencia de un entrenador',
    description=(
        'Devuelve el perfil del entrenador junto con su historial de '
        'entradas/salidas y totales. Admite filtro opcional por rango de fechas.'
    ),
    parameters=[
        OpenApiParameter(
            name='date_from', type=OpenApiTypes.DATE, required=False,
            description='Fecha inicial del historial (YYYY-MM-DD)',
        ),
        OpenApiParameter(
            name='date_to', type=OpenApiTypes.DATE, required=False,
            description='Fecha final del historial (YYYY-MM-DD)',
        ),
    ],
    responses={
        200: CoachHistorySerializer,
        400: DetailMessageSerializer,
        404: DetailMessageSerializer,
    },
)
class CoachHistoryView(views.APIView):
    """
    GET /api/coaches/{id}/history/
    Historial de asistencia del entrenador (solo check-in/check-out).
    """
    permission_classes = [IsAdminOrReceptionist]

    def get(self, request, pk):
        try:
            coach = Coach.objects.get(pk=pk)
        except Coach.DoesNotExist:
            return Response(
                {'detail': 'Coach not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        date_from, date_to, error = _parse_date_range(request)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        attendances = CoachAttendance.objects.filter(coach=coach)
        if date_from:
            attendances = attendances.filter(check_in__date__gte=date_from)
        if date_to:
            attendances = attendances.filter(check_in__date__lte=date_to)
        attendances = attendances.order_by('-check_in')

        completed = attendances.filter(check_out__isnull=False)
        total_minutes = sum(
            attendance.duration_minutes or 0
            for attendance in completed.only('check_in', 'check_out')
        )

        open_attendance = CoachAttendance.objects.filter(
            coach=coach, check_out__isnull=True,
        ).order_by('-check_in').first()

        summary = {
            'total_attendances': attendances.count(),
            'total_minutes': total_minutes,
            'currently_inside': open_attendance is not None,
            'open_attendance_id': open_attendance.id if open_attendance else None,
            'first_attendance': attendances.order_by('check_in').values_list(
                'check_in', flat=True,
            ).first(),
            'last_attendance': attendances.order_by('-check_in').values_list(
                'check_in', flat=True,
            ).first(),
        }

        data = {
            'coach': coach,
            'summary': summary,
            'attendances': attendances,
        }
        return Response(CoachHistorySerializer(data).data)


@extend_schema(
    tags=['coaches'],
    summary='Registrar entrada de un entrenador',
    description=(
        'Registra la entrada del entrenador al gimnasio. Devuelve 404 si el '
        'entrenador no existe o está inactivo, y 400 si ya tiene una entrada abierta.'
    ),
    request=None,
    responses={
        201: CoachAttendanceSerializer,
        400: ErrorMessageSerializer,
        404: ErrorMessageSerializer,
    },
)
class CoachCheckInView(views.APIView):
    """
    POST /api/coaches/{id}/check-in/
    """
    permission_classes = [IsAdminOrReceptionist]

    def post(self, request, pk):
        try:
            coach = Coach.objects.get(pk=pk, is_active=True)
        except Coach.DoesNotExist:
            return Response(
                {'error': 'Coach not found or inactive'},
                status=status.HTTP_404_NOT_FOUND,
            )

        active_attendance = CoachAttendance.objects.filter(
            coach=coach, check_out__isnull=True,
        ).first()

        if active_attendance:
            return Response(
                {
                    'error': 'Coach is already checked in',
                    'attendance_id': active_attendance.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        attendance = CoachAttendance.objects.create(
            coach=coach,
            check_in=timezone.now(),
            registered_by=request.user,
        )
        return Response(
            CoachAttendanceSerializer(attendance).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=['coaches'],
    summary='Registrar salida de un entrenador',
    description='Cierra la asistencia abierta del entrenador. Devuelve 404 si no hay entrada abierta.',
    request=None,
    responses={200: CoachAttendanceSerializer, 404: ErrorMessageSerializer},
)
class CoachCheckOutView(views.APIView):
    """
    POST /api/coaches/{id}/check-out/
    """
    permission_classes = [IsAdminOrReceptionist]

    def post(self, request, pk):
        try:
            attendance = CoachAttendance.objects.get(
                coach_id=pk, check_out__isnull=True,
            )
        except CoachAttendance.DoesNotExist:
            return Response(
                {'error': 'Active coach attendance not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        attendance.check_out = timezone.now()
        attendance.save(update_fields=['check_out'])
        return Response(CoachAttendanceSerializer(attendance).data)
