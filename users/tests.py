from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class AuthFlowTests(APITestCase):
    """Pruebas de integración del módulo de autenticación JWT (users)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_test',
            password='admin1234',
            role=User.Role.ADMIN,
        )
        self.admin.is_staff = True
        self.admin.save(update_fields=['is_staff'])

        self.receptionist = User.objects.create_user(
            username='recepcion_test',
            password='recepcion123',
            role=User.Role.RECEPTIONIST,
        )
        self.login_url = reverse('auth-login')

    def test_login_returns_tokens_and_profile(self):
        response = self.client.post(
            self.login_url,
            {'username': 'admin_test', 'password': 'admin1234'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'admin_test')
        self.assertEqual(response.data['user']['role'], User.Role.ADMIN)

    def test_login_with_wrong_password_is_rejected(self):
        response = self.client.post(
            self.login_url,
            {'username': 'admin_test', 'password': 'clave_mala'},
            format='json',
        )

        self.assertIn(response.status_code, (400, 401))

    def test_refresh_rotates_access_token(self):
        login = self.client.post(
            self.login_url,
            {'username': 'admin_test', 'password': 'admin1234'},
            format='json',
        )
        refresh = login.data['refresh']

        response = self.client.post(
            reverse('auth-refresh'), {'refresh': refresh}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse('auth-me'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_own_profile(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.get(reverse('auth-me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'recepcion_test')
        self.assertEqual(response.data['role'], User.Role.RECEPTIONIST)

    def test_me_does_not_expose_role_changes(self):
        """El usuario no puede auto-asignarse otro rol desde /auth/me/."""
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.patch(
            reverse('auth-me'), {'role': User.Role.ADMIN}, format='json'
        )

        self.receptionist.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.receptionist.role, User.Role.RECEPTIONIST)


class StaffManagementTests(APITestCase):
    """Pruebas de integración de la gestión de usuarios del staff (/api/users/)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='jefe',
            password='jefe12345',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.receptionist = User.objects.create_user(
            username='recepcion',
            password='recepcion123',
            role=User.Role.RECEPTIONIST,
        )
        self.list_url = reverse('user-list')

    def test_list_requires_admin_role(self):
        self.client.force_authenticate(user=self.receptionist)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user_hashes_password_and_rejects_short_password(self):
        self.client.force_authenticate(user=self.admin)

        invalido = self.client.post(
            self.list_url,
            {
                'username': 'corto',
                'password': '1234',
                'role': User.Role.RECEPTIONIST,
            },
            format='json',
        )
        self.assertEqual(invalido.status_code, status.HTTP_400_BAD_REQUEST)

        valido = self.client.post(
            self.list_url,
            {
                'username': 'nuevo_staff',
                'password': 'secreta123',
                'role': User.Role.RECEPTIONIST,
                'email': 'staff@fitweb.test',
            },
            format='json',
        )
        self.assertEqual(valido.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', valido.data)

        # La contraseña se guardó hasheada y sirve para iniciar sesión.
        creado = User.objects.get(username='nuevo_staff')
        self.assertTrue(creado.check_password('secreta123'))
        login = self.client.post(
            reverse('auth-login'),
            {'username': 'nuevo_staff', 'password': 'secreta123'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_role_update_synchronizes_staff_flag(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-detail', args=[self.receptionist.id])

        response = self.client.patch(
            url, {'role': User.Role.ADMIN}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.receptionist.refresh_from_db()
        self.assertTrue(self.receptionist.is_staff)
