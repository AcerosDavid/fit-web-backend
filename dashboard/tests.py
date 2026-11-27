from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from attendance.models import Attendance
from members.models import Member
from memberships.models import Membership
from payments.models import Payment
from plans.models import Plan
from users.models import User


class DashboardStatsTests(APITestCase):
    """Pruebas de integración del dashboard (dashboard)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_d',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.member = Member.objects.create(
            first_name='Hugo',
            last_name='León',
            email='hugo@fitweb.test',
        )
        self.plan = Plan.objects.create(
            name='Mensual Básico', price='29.99', duration_days=30
        )

    def _create_scenario(self):
        hoy = timezone.localdate()
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=hoy,
            end_date=hoy + timezone.timedelta(days=3),
        )
        Payment.objects.create(
            membership=membership, amount='29.99', received_by=self.admin
        )
        # Asistencia registrada ahora (hoy en la zona horaria local del servidor).
        Attendance.objects.create(member=self.member, check_in=timezone.now())
        return membership

    def test_metrics_aggregate_created_data(self):
        self._create_scenario()
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse('dashboard-stats'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_members'], 1)
        self.assertEqual(response.data['monthly_revenue'], 29.99)
        self.assertEqual(response.data['todays_attendance'], 1)
        self.assertEqual(response.data['expiring_memberships'], 1)
        self.assertEqual(
            response.data['month'], timezone.localdate().strftime('%B %Y')
        )

    def test_metrics_are_empty_without_business_activity(self):
        """Solo existe el cliente del setUp: no hay cobros, visitas ni vencimientos."""
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse('dashboard-stats'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_members'], 1)
        self.assertEqual(response.data['monthly_revenue'], 0.0)
        self.assertEqual(response.data['todays_attendance'], 0)
        self.assertEqual(response.data['expiring_memberships'], 0)

    def test_dashboard_is_restricted_to_admin_or_receptionist(self):
        coach_user = User.objects.create_user(
            username='entrenador_d',
            password='entrenador123',
            role=User.Role.COACH,
        )
        self.client.force_authenticate(user=coach_user)

        response = self.client.get(reverse('dashboard-stats'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
