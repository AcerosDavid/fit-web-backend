from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum
from members.models import Member
from memberships.models import Membership
from payments.models import Payment
from attendance.models import Attendance
from members.views import IsAdminOrReceptionist

class DashboardStatsView(APIView):
    """
    GET /api/dashboard/
    Retorna métricas clave para el panel de administración.
    """
    permission_classes = [IsAdminOrReceptionist]

    def get(self, request):
        now = timezone.now()
        today = now.date()
        first_day_of_month = today.replace(day=1)

        # 1. Total de miembros activos
        active_members_count = Member.objects.filter(status=Member.Status.ACTIVE).count()

        # 2. Ingresos del mes actual
        monthly_revenue_agg = Payment.objects.filter(
            payment_date__gte=first_day_of_month
        ).aggregate(total=Sum('amount'))
        monthly_revenue = monthly_revenue_agg['total'] or 0

        # 3. Asistencias de hoy (gente que vino al gimnasio hoy)
        todays_attendance = Attendance.objects.filter(
            check_in__date=today
        ).count()

        # 4. Membresías que vencen en los próximos 7 días
        next_week = today + timezone.timedelta(days=7)
        expiring_memberships = Membership.objects.filter(
            status=Membership.Status.ACTIVE,
            end_date__gte=today,
            end_date__lte=next_week
        ).count()

        return Response({
            "active_members": active_members_count,
            "monthly_revenue": float(monthly_revenue),
            "todays_attendance": todays_attendance,
            "expiring_memberships": expiring_memberships,
            "month": today.strftime("%B %Y")
        })
