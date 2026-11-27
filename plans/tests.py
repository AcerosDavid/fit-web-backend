from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from plans.models import Plan
from users.models import User


class PlanApiTests(APITestCase):
    """Pruebas de integración del catálogo de planes (plans)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_p',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.receptionist = User.objects.create_user(
            username='recepcion_p',
            password='recepcion123',
            role=User.Role.RECEPTIONIST,
        )
        self.plan = Plan.objects.create(
            name='Mensual Básico',
            price='29.99',
            duration_days=30,
        )
        self.list_url = reverse('plan-list')

    def test_receptionist_can_list_but_not_create(self):
        self.client.force_authenticate(user=self.receptionist)

        listado = self.client.get(self.list_url)
        self.assertEqual(listado.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listado.data), 1)

        creado = self.client.post(
            self.list_url,
            {'name': 'Trimestral', 'price': '79.99', 'duration_days': 90},
            format='json',
        )
        self.assertEqual(creado.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Plan.objects.count(), 1)

    def test_admin_creates_and_updates_plan(self):
        self.client.force_authenticate(user=self.admin)

        creado = self.client.post(
            self.list_url,
            {'name': 'Anual Premium', 'price': '299.99', 'duration_days': 365},
            format='json',
        )
        self.assertEqual(creado.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Plan.objects.count(), 2)

        detalle = reverse('plan-detail', args=[creado.data['id']])
        actualizado = self.client.patch(
            detalle, {'price': '249.99'}, format='json'
        )
        self.assertEqual(actualizado.status_code, status.HTTP_200_OK)
        self.assertEqual(str(actualizado.data['price']), '249.99')

    def test_anonymous_user_is_rejected(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
