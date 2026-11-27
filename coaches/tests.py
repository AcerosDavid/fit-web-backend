from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from coaches.models import Coach, CoachAttendance
from users.models import User


class CoachApiTests(APITestCase):
    """Pruebas de integración del módulo de entrenadores (coaches)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_c',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.coach = Coach.objects.create(
            first_name='Marta',
            last_name='Díaz',
            specialty='Crossfit',
        )
        self.list_url = reverse('coach-list')

    def test_create_and_list_coaches(self):
        self.client.force_authenticate(user=self.admin)

        creado = self.client.post(
            self.list_url,
            {'first_name': 'Iván', 'last_name': 'Ríos', 'specialty': 'Pesas'},
            format='json',
        )
        self.assertEqual(creado.status_code, status.HTTP_201_CREATED)
        self.assertEqual(creado.data['qr_code'], f"FIT-C-{creado.data['id']}")

        listado = self.client.get(self.list_url)
        self.assertEqual(len(listado.data), 2)

    def test_check_in_and_check_out_flow(self):
        self.client.force_authenticate(user=self.admin)
        check_in_url = reverse('coach-check-in', args=[self.coach.id])
        check_out_url = reverse('coach-check-out', args=[self.coach.id])

        entrada = self.client.post(check_in_url)
        self.assertEqual(entrada.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(entrada.data['check_out'])

        repetida = self.client.post(check_in_url)
        self.assertEqual(repetida.status_code, status.HTTP_400_BAD_REQUEST)

        salida = self.client.post(check_out_url)
        self.assertEqual(salida.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(salida.data['check_out'])

        sin_entrada = self.client.post(check_out_url)
        self.assertEqual(sin_entrada.status_code, status.HTTP_404_NOT_FOUND)

    def test_coach_history_aggregates_attendance(self):
        ahora = timezone.now()
        CoachAttendance.objects.create(
            coach=self.coach,
            check_in=ahora - timedelta(hours=3),
            check_out=ahora - timedelta(hours=2),
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            reverse('coach-history', args=[self.coach.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['total_attendances'], 1)
        self.assertEqual(response.data['summary']['total_minutes'], 60)
        self.assertFalse(response.data['summary']['currently_inside'])

    def test_delete_coach_is_a_soft_delete(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            reverse('coach-detail', args=[self.coach.id])
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.coach.refresh_from_db()
        self.assertFalse(self.coach.is_active)
        self.assertEqual(Coach.objects.count(), 1)  # sigue en la BD

        listado = self.client.get(self.list_url)
        self.assertEqual(len(listado.data), 0)  # oculto del listado
