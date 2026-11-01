from decimal import Decimal

from django.db.models import Sum
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from members.models import Member
from members.serializers import MemberSerializer
from memberships.models import Membership
from payments.models import Payment
from attendance.models import Attendance
from plans.serializers import PlanSerializer


class MemberBriefSerializer(serializers.ModelSerializer):
    """Datos mínimos del cliente para la línea de tiempo global."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = ('id', 'full_name', 'email', 'phone', 'status')


class MembershipHistorySerializer(serializers.ModelSerializer):
    """Membresía con su plan y totales de pago asociados."""

    plan_details = PlanSerializer(source='plan', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    payment_count = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = (
            'id', 'plan', 'plan_details', 'start_date', 'end_date', 'status',
            'is_valid', 'created_by', 'payment_count', 'total_paid',
            'created_at', 'updated_at',
        )

    @extend_schema_field(serializers.IntegerField)
    def get_payment_count(self, obj):
        count = getattr(obj, 'payment_count', None)
        if count is None:
            count = obj.payments.count()
        return count

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total_paid(self, obj):
        total = getattr(obj, 'total_paid', None)
        if total is None:
            total = obj.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return Decimal(total).quantize(Decimal('0.01'))


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Pago con el nombre del plan de la membresía asociada."""

    membership_plan = serializers.CharField(source='membership.plan.name', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'membership', 'membership_plan', 'amount', 'payment_date',
            'method', 'method_display', 'notes', 'received_by', 'created_at',
        )


class AttendanceHistorySerializer(serializers.ModelSerializer):
    """Asistencia con la duración de la visita en minutos."""

    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ('id', 'check_in', 'check_out', 'duration_minutes', 'registered_by')

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_duration_minutes(self, obj):
        if obj.check_out and obj.check_in:
            return int((obj.check_out - obj.check_in).total_seconds() // 60)
        return None


class HistorySummarySerializer(serializers.Serializer):
    """Totales del historial de un cliente."""

    total_memberships = serializers.IntegerField()
    active_membership = MembershipHistorySerializer(allow_null=True)
    total_payments = serializers.IntegerField()
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_attendances = serializers.IntegerField()
    first_attendance = serializers.DateTimeField(allow_null=True)
    last_attendance = serializers.DateTimeField(allow_null=True)
    member_since = serializers.DateTimeField()


class MemberHistorySerializer(serializers.Serializer):
    """Historial agregado de un cliente."""

    member = MemberSerializer()
    summary = HistorySummarySerializer()
    memberships = MembershipHistorySerializer(many=True)
    payments = PaymentHistorySerializer(many=True)
    attendances = AttendanceHistorySerializer(many=True)


class HistoryEventType:
    MEMBERSHIP = 'membership'
    PAYMENT = 'payment'
    ATTENDANCE = 'attendance'

    CHOICES = (
        (MEMBERSHIP, 'Membership'),
        (PAYMENT, 'Payment'),
        (ATTENDANCE, 'Attendance'),
    )


class HistoryEventSerializer(serializers.Serializer):
    """Evento unificado de la línea de tiempo global."""

    type = serializers.ChoiceField(choices=HistoryEventType.CHOICES)
    event = serializers.CharField()
    date = serializers.DateTimeField()
    member = MemberBriefSerializer()
    reference_id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True, required=False,
    )
    metadata = serializers.DictField(required=False, allow_null=True)


class HistoryEventListSerializer(serializers.Serializer):
    """Lista paginada de eventos del historial global."""

    count = serializers.IntegerField()
    results = HistoryEventSerializer(many=True)
