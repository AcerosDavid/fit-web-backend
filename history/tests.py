from datetime import timedelta

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


class MemberHistoryTests(APITestCase):
    """Pruebas de integración del historial por cliente (/api/members/{id}/history/)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_h',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.member = Member.objects.create(
            first_name='Elena',
            last_name='Vega',
            email='elena@fitweb.test',
        )
        self.plan = Plan.objects.create(
            name='Mensual Básico', price='29.99', duration_days=30
        )
        self.membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            end_date=timezone.localdate() + timedelta(days=20),
        )
        Payment.objects.create(
            membership=self.membership, amount='29.99', received_by=self.admin
        )
        Attendance.objects.create(member=self.member)
        self.url = reverse('member-history', args=[self.member.id])
        self.client.force_authenticate(user=self.admin)

    def test_history_returns_sections_and_totals(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['member']['id'], self.member.id)
        self.assertEqual(response.data['summary']['total_memberships'], 1)
        self.assertEqual(response.data['summary']['total_payments'], 1)
        self.assertEqual(float(response.data['summary']['total_paid']), 29.99)
        self.assertEqual(response.data['summary']['total_attendances'], 1)
        self.assertEqual(len(response.data['memberships']), 1)
        self.assertEqual(len(response.data['payments']), 1)
        self.assertEqual(len(response.data['attendances']), 1)

    def test_history_filters_by_date_range(self):
        response = self.client.get(
            self.url, {'date_from': '2000-01-01', 'date_to': '2000-01-31'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['total_memberships'], 0)
        self.assertEqual(response.data['summary']['total_payments'], 0)

    def test_history_rejects_invalid_dates(self):
        mal_formada = self.client.get(self.url, {'date_from': '31-12-2025'})
        invertida = self.client.get(
            self.url, {'date_from': '2026-01-10', 'date_to': '2026-01-01'}
        )

        self.assertEqual(mal_formada.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invertida.status_code, status.HTTP_400_BAD_REQUEST)

    def test_history_of_missing_member_returns_404(self):
        response = self.client.get(reverse('member-history', args=[9999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GlobalHistoryTests(APITestCase):
    """Pruebas de integración de la línea de tiempo global (/api/history/)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_gh',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.member = Member.objects.create(
            first_name='Pablo',
            last_name='Sena',
            email='pablo@fitweb.test',
        )
        self.plan = Plan.objects.create(
            name='Trimestral Pro', price='79.99', duration_days=90
        )
        self.membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            end_date=timezone.localdate() + timedelta(days=60),
        )
        Payment.objects.create(
            membership=self.membership, amount='79.99', received_by=self.admin
        )
        Attendance.objects.create(member=self.member)
        self.url = reverse('global-history')
        self.client.force_authenticate(user=self.admin)

    def test_timeline_is_sorted_newest_first(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        fechas = [evento['date'] for evento in response.data['results']]
        self.assertEqual(fechas, sorted(fechas, reverse=True))

    def test_filter_by_event_type(self):
        response = self.client.get(self.url, {'type': 'payment'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['type'], 'payment')

    def test_pagination_with_limit_and_offset(self):
        limitado = self.client.get(self.url, {'limit': 2})
        desplazado = self.client.get(self.url, {'limit': 2, 'offset': 2})

        self.assertEqual(len(limitado.data['results']), 2)
        self.assertEqual(desplazado.data['count'], 3)
        self.assertEqual(len(desplazado.data['results']), 1)

    def test_rejects_invalid_query_params(self):
        for params in (
            {'limit': 'abc'},
            {'offset': 'cerca'},
            {'type': 'inventado'},
            {'member': 'x'},
        ):
            response = self.client.get(self.url, params)
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST, params
            )
