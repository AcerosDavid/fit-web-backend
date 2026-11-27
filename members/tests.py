from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from members.models import Member
from users.models import User


class MemberApiTests(APITestCase):
    """Pruebas de integración del módulo de clientes (members)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_m',
            password='admin1234',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.receptionist = User.objects.create_user(
            username='recepcion_m',
            password='recepcion123',
            role=User.Role.RECEPTIONIST,
        )
        self.coach_user = User.objects.create_user(
            username='entrenador_m',
            password='entrenador123',
            role=User.Role.COACH,
        )
        self.member = Member.objects.create(
            first_name='Ana',
            last_name='Pérez',
            email='ana@fitweb.test',
            phone='3001112233',
        )
        self.list_url = reverse('member-list')

    def test_coach_role_cannot_access_members(self):
        self.client.force_authenticate(user=self.coach_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_and_create_member(self):
        self.client.force_authenticate(user=self.receptionist)

        listado = self.client.get(self.list_url)
        self.assertEqual(listado.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listado.data), 1)

        creado = self.client.post(
            self.list_url,
            {
                'first_name': 'Luis',
                'last_name': 'Gómez',
                'email': 'luis@fitweb.test',
                'gender': 'MALE',
            },
            format='json',
        )
        self.assertEqual(creado.status_code, status.HTTP_201_CREATED)

        # El serializer de creación no devuelve id ni QR: se consulta el detalle.
        nuevo = Member.objects.get(email='luis@fitweb.test')
        detalle = self.client.get(reverse('member-detail', args=[nuevo.id]))
        self.assertEqual(detalle.data['qr_code'], f"FIT-M-{nuevo.id}")

    def test_create_member_rejects_duplicate_email(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.post(
            self.list_url,
            {'first_name': 'Otro', 'last_name': 'Cliente', 'email': 'ana@fitweb.test'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_soft_delete_keeps_record_and_hides_it_from_list(self):
        self.client.force_authenticate(user=self.receptionist)
        url = reverse('member-detail', args=[self.member.id])
        delete_url = reverse('member-delete', args=[self.member.id])

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # El registro sigue en la base de datos (soft-delete)...
        self.member.refresh_from_db()
        self.assertIsNotNone(self.member.deleted_at)
        self.assertEqual(Member.all_objects.count(), 1)
        # ...pero desaparece de los listados.
        listado = self.client.get(self.list_url)
        self.assertEqual(len(listado.data), 0)
        detalle = self.client.get(url)
        self.assertEqual(detalle.status_code, status.HTTP_404_NOT_FOUND)

    def test_restore_requires_admin(self):
        self.member.delete()  # soft-delete

        self.client.force_authenticate(user=self.receptionist)
        restore_url = reverse('member-restore', args=[self.member.id])
        denegado = self.client.post(restore_url)
        self.assertEqual(denegado.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        permitido = self.client.post(restore_url)
        self.assertEqual(permitido.status_code, status.HTTP_200_OK)

        self.member.refresh_from_db()
        self.assertIsNone(self.member.deleted_at)
        listado = self.client.get(self.list_url)
        self.assertEqual(len(listado.data), 1)

    def test_restore_of_active_member_returns_400(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse('member-restore', args=[self.member.id])
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
