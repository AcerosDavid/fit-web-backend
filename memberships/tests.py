from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from members.models import Member
from memberships.models import Membership
from plans.models import Plan
from users.models import User


class MembershipApiTests(APITestCase):
    """Pruebas de integración de membresías (memberships)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_me',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.member = Member.objects.create(
            first_name='Carla',
            last_name='Ruiz',
            email='carla@fitweb.test',
        )
        self.plan = Plan.objects.create(
            name='Trimestral Pro',
            price='79.99',
            duration_days=90,
        )
        self.list_url = reverse('membership-list')

    def test_create_membership_calculates_end_date_and_creator(self):
        self.client.force_authenticate(user=self.admin)
        hoy = timezone.localdate()

        response = self.client.post(
            self.list_url,
            {'member': self.member.id, 'plan': self.plan.id, 'start_date': hoy},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['end_date'], (hoy + timedelta(days=90)).isoformat())
        self.assertEqual(response.data['created_by'], self.admin.id)
        self.assertTrue(response.data['is_valid'])

    def test_filter_by_member_query_param(self):
        otro = Member.objects.create(
            first_name='Diego',
            last_name='Sanz',
            email='diego@fitweb.test',
        )
        Membership.objects.create(
            member=self.member, plan=self.plan, end_date=timezone.localdate()
        )
        Membership.objects.create(
            member=otro, plan=self.plan, end_date=timezone.localdate()
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.list_url, {'member': self.member.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['member'], self.member.id)

    def test_cancelling_membership_invalidates_it(self):
        membership = Membership.objects.create(
            member=self.member, plan=self.plan, end_date=timezone.localdate()
        )
        self.client.force_authenticate(user=self.admin)

        detalle = reverse('membership-detail', args=[membership.id])
        response = self.client.patch(
            detalle, {'status': Membership.Status.CANCELLED}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership.refresh_from_db()
        self.assertFalse(membership.is_valid)
