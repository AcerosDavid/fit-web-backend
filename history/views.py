from datetime import datetime, time
from decimal import Decimal

from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.models import Attendance
from config.serializers import DetailMessageSerializer
from members.models import Member
from members.views import IsAdminOrReceptionist
from memberships.models import Membership
from payments.models import Payment
from .serializers import (
    AttendanceHistorySerializer,
    HistoryEventListSerializer,
    HistoryEventType,
    MemberHistorySerializer,
    MembershipHistorySerializer,
    PaymentHistorySerializer,
)

MAX_EVENT_LIMIT = 500
DEFAULT_EVENT_LIMIT = 100

TOTAL_PAID_FIELD = DecimalField(max_digits=12, decimal_places=2)


def _annotate_memberships(queryset):
    """Agrega conteo y suma de pagos por membresía en una sola query."""
    return queryset.select_related('plan').annotate(
        payment_count=Count('payments', distinct=True),
        total_paid=Coalesce(
            Sum('payments__amount'), Decimal('0'), output_field=TOTAL_PAID_FIELD,
        ),
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


def _filter_by_date(queryset, field, date_from, date_to):
    if date_from:
        queryset = queryset.filter(**{f'{field}__gte': date_from})
    if date_to:
        queryset = queryset.filter(**{f'{field}__lte': date_to})
    return queryset


def _membership_event_date(membership):
    """Convierte start_date en un datetime para ordenar la línea de tiempo."""
    value = datetime.combine(membership.start_date, time.min)
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    return value


def _attendance_metadata(attendance):
    metadata = {
        'check_out': attendance.check_out.isoformat() if attendance.check_out else None,
    }
    if attendance.check_out and attendance.check_in:
        metadata['duration_minutes'] = int(
            (attendance.check_out - attendance.check_in).total_seconds() // 60
        )
    return metadata


@extend_schema(
    tags=['history'],
    summary='Historial agregado de un cliente',
    description=(
        'Devuelve el perfil del cliente junto con sus membresías, pagos y '
        'asistencias, más totales consolidados. Admite filtro opcional por rango '
        'de fechas (aplicado a cada sección). Incluye clientes soft-deletados.'
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
        200: MemberHistorySerializer,
        400: DetailMessageSerializer,
        404: DetailMessageSerializer,
    },
)
class MemberHistoryView(APIView):
    """
    GET /api/members/{id}/history/
    Historial completo de un cliente: membresías, pagos, asistencias y totales.
    """
    permission_classes = [IsAdminOrReceptionist]

    def get(self, request, pk):
        try:
            member = Member.all_objects.get(pk=pk)
        except Member.DoesNotExist:
            return Response(
                {'detail': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND,
            )

        date_from, date_to, error = _parse_date_range(request)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        memberships = _filter_by_date(
            _annotate_memberships(member.memberships.all()),
            'start_date', date_from, date_to,
        ).order_by('-start_date')

        payments = _filter_by_date(
            Payment.objects.filter(membership__member=member).select_related(
                'membership__plan',
            ),
            'payment_date__date', date_from, date_to,
        ).order_by('-payment_date')

        attendances = _filter_by_date(
            Attendance.objects.filter(member=member),
            'check_in__date', date_from, date_to,
        ).order_by('-check_in')

        total_paid = payments.aggregate(
            total=Coalesce(
                Sum('amount'), Decimal('0'), output_field=TOTAL_PAID_FIELD,
            ),
        )['total']

        active_membership = _annotate_memberships(
            member.memberships.filter(
                status=Membership.Status.ACTIVE,
                end_date__gte=timezone.localdate(),
            ),
        ).order_by('-end_date').first()

        summary = {
            'total_memberships': memberships.count(),
            'active_membership': active_membership,
            'total_payments': payments.count(),
            'total_paid': total_paid,
            'total_attendances': attendances.count(),
            'first_attendance': attendances.order_by('check_in').values_list(
                'check_in', flat=True,
            ).first(),
            'last_attendance': attendances.order_by('-check_in').values_list(
                'check_in', flat=True,
            ).first(),
            'member_since': member.created_at,
        }

        data = {
            'member': member,
            'summary': summary,
            'memberships': memberships,
            'payments': payments,
            'attendances': attendances,
        }
        return Response(MemberHistorySerializer(data).data)


@extend_schema(
    tags=['history'],
    summary='Historial global del gimnasio',
    description=(
        'Línea de tiempo unificada de membresías, pagos y asistencias de todos '
        'los clientes, ordenada de más reciente a más antigua. Filtrable por '
        'cliente, tipo de evento y rango de fechas, con paginación simple.'
    ),
    parameters=[
        OpenApiParameter(
            name='member', type=OpenApiTypes.INT, required=False,
            description='Filtra por ID de cliente',
        ),
        OpenApiParameter(
            name='type', type=OpenApiTypes.STR, required=False,
            description=(
                'Tipos separados por coma: membership, payment, attendance. '
                'Por defecto devuelve todos.'
            ),
        ),
        OpenApiParameter(
            name='date_from', type=OpenApiTypes.DATE, required=False,
            description='Fecha inicial de los eventos (YYYY-MM-DD)',
        ),
        OpenApiParameter(
            name='date_to', type=OpenApiTypes.DATE, required=False,
            description='Fecha final de los eventos (YYYY-MM-DD)',
        ),
        OpenApiParameter(
            name='limit', type=OpenApiTypes.INT, required=False,
            description=f'Máximo de eventos a devolver (default {DEFAULT_EVENT_LIMIT}, max {MAX_EVENT_LIMIT})',
        ),
        OpenApiParameter(
            name='offset', type=OpenApiTypes.INT, required=False,
            description='Cantidad de eventos a omitir (default 0)',
        ),
    ],
    responses={200: HistoryEventListSerializer, 400: DetailMessageSerializer},
)
class GlobalHistoryView(APIView):
    """
    GET /api/history/
    Línea de tiempo global de membresías, pagos y asistencias.
    """
    permission_classes = [IsAdminOrReceptionist]

    def get(self, request):
        date_from, date_to, error = _parse_date_range(request)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        member_id, error = self._parse_int_param(request, 'member')
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        limit, error = self._parse_int_param(request, 'limit', DEFAULT_EVENT_LIMIT)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)
        limit = max(1, min(limit, MAX_EVENT_LIMIT))

        offset, error = self._parse_int_param(request, 'offset', 0)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)
        offset = max(0, offset)

        types, error = self._parse_types(request)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        events = []
        if HistoryEventType.MEMBERSHIP in types:
            events.extend(self._membership_events(member_id, date_from, date_to))
        if HistoryEventType.PAYMENT in types:
            events.extend(self._payment_events(member_id, date_from, date_to))
        if HistoryEventType.ATTENDANCE in types:
            events.extend(self._attendance_events(member_id, date_from, date_to))

        events.sort(key=lambda event: event['date'], reverse=True)
        total = len(events)
        page = events[offset:offset + limit]

        data = {'count': total, 'results': page}
        return Response(HistoryEventListSerializer(data).data)

    def _membership_events(self, member_id, date_from, date_to):
        queryset = Membership.objects.select_related('member', 'plan')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        queryset = _filter_by_date(queryset, 'start_date', date_from, date_to)

        return [
            {
                'type': HistoryEventType.MEMBERSHIP,
                'event': 'membership_started',
                'date': _membership_event_date(membership),
                'member': membership.member,
                'reference_id': membership.id,
                'title': f'Membresía {membership.plan.name}',
                'description': (
                    f'{membership.get_status_display()} · '
                    f'{membership.start_date} → {membership.end_date}'
                ),
                'amount': membership.plan.price,
                'metadata': {
                    'plan_id': membership.plan_id,
                    'status': membership.status,
                    'end_date': membership.end_date.isoformat(),
                },
            }
            for membership in queryset
        ]

    def _payment_events(self, member_id, date_from, date_to):
        queryset = Payment.objects.select_related(
            'membership__member', 'membership__plan',
        )
        if member_id:
            queryset = queryset.filter(membership__member_id=member_id)
        queryset = _filter_by_date(queryset, 'payment_date__date', date_from, date_to)

        return [
            {
                'type': HistoryEventType.PAYMENT,
                'event': 'payment_received',
                'date': payment.payment_date,
                'member': payment.membership.member,
                'reference_id': payment.id,
                'title': f'Pago · {payment.get_method_display()}',
                'description': payment.notes or f'Membresía {payment.membership.plan.name}',
                'amount': payment.amount,
                'metadata': {
                    'membership_id': payment.membership_id,
                    'method': payment.method,
                },
            }
            for payment in queryset
        ]

    def _attendance_events(self, member_id, date_from, date_to):
        queryset = Attendance.objects.select_related('member')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        queryset = _filter_by_date(queryset, 'check_in__date', date_from, date_to)

        return [
            {
                'type': HistoryEventType.ATTENDANCE,
                'event': 'check_in',
                'date': attendance.check_in,
                'member': attendance.member,
                'reference_id': attendance.id,
                'title': 'Check-in',
                'description': (
                    f'Salida: {attendance.check_out.isoformat()}'
                    if attendance.check_out else 'Sin check-out registrado'
                ),
                'amount': None,
                'metadata': _attendance_metadata(attendance),
            }
            for attendance in queryset
        ]

    @staticmethod
    def _parse_int_param(request, name, default=None):
        raw = request.query_params.get(name)
        if raw in (None, ''):
            return default, None
        try:
            return int(raw), None
        except (TypeError, ValueError):
            return None, f"Invalid '{name}' value. Use an integer."

    @staticmethod
    def _parse_types(request):
        allowed = {
            HistoryEventType.MEMBERSHIP,
            HistoryEventType.PAYMENT,
            HistoryEventType.ATTENDANCE,
        }
        raw_values = request.query_params.getlist('type')
        if not raw_values:
            return allowed, None

        requested = set()
        for raw in raw_values:
            requested.update(
                value.strip().lower() for value in raw.split(',') if value.strip()
            )

        invalid = requested - allowed
        if invalid:
            return None, (
                f"Invalid 'type' value(s): {', '.join(sorted(invalid))}. "
                f"Allowed: {', '.join(sorted(allowed))}."
            )
        return requested or allowed, None
