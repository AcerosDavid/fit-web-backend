from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from members.models import Member
from memberships.models import Membership
from payments.models import Payment
from plans.models import Plan
from users.models import User


class PaymentApiTests(APITestCase):
    """Pruebas de integración de la registración de pagos (payments)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_pg',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.member = Member.objects.create(
            first_name='Sofía',
            last_name='Mora',
            email='sofia@fitweb.test',
        )
        self.plan = Plan.objects.create(
            name='Mensual Básico', price='29.99', duration_days=30
        )
        self.membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            end_date=timezone.localdate() + timezone.timedelta(days=30),
        )
        self.list_url = reverse('payment-list')

    def test_create_payment_registers_the_receiver(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            self.list_url,
            {
                'membership': self.membership.id,
                'amount': '29.99',
                'method': Payment.Method.CASH,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['received_by'], self.admin.id)
        self.assertEqual(Payment.objects.count(), 1)

    def test_filter_payments_by_membership_and_member(self):
        otro_plan = Plan.objects.create(
            name='Trimestral', price='79.99', duration_days=90
        )
        otra_membresia = Membership.objects.create(
            member=self.member,
            plan=otro_plan,
            end_date=timezone.localdate() + timezone.timedelta(days=90),
        )
        Payment.objects.create(
            membership=self.membership, amount='29.99', received_by=self.admin
        )
        Payment.objects.create(
            membership=otra_membresia, amount='79.99', received_by=self.admin
        )
        self.client.force_authenticate(user=self.admin)

        por_membresia = self.client.get(
            self.list_url, {'membership': self.membership.id}
        )
        por_cliente = self.client.get(self.list_url, {'member': self.member.id})
        combinado = self.client.get(
            self.list_url, {'member': self.member.id, 'membership': otra_membresia.id}
        )

        self.assertEqual(len(por_membresia.data), 1)
        self.assertEqual(por_membresia.data[0]['membership'], self.membership.id)
        self.assertEqual(len(por_cliente.data), 2)
        self.assertEqual(len(combinado.data), 1)
        self.assertEqual(combinado.data[0]['membership'], otra_membresia.id)

    def test_payment_list_requires_authentication(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Payment.objects.count(), 0)
