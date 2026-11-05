from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from attendance.models import Attendance
from coaches.models import Coach, CoachAttendance
from members.models import Member
from users.models import User

BOGOTA = ZoneInfo('America/Bogota')


def local_datetime(day, hour, minute=0, second=0):
    return datetime.combine(day, time(hour, minute, second), tzinfo=BOGOTA)


class AttendanceTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='recepcion', password='secret', role=User.Role.RECEPTIONIST,
        )
        self.client.force_authenticate(self.user)
        self.member = Member.objects.create(
            first_name='Ana', last_name='Pérez', email='ana@example.com',
        )
        self.coach = Coach.objects.create(
            first_name='Luis', last_name='Gómez', specialty='Pesas',
        )
        self.yesterday = timezone.localdate() - timedelta(days=1)
        self.end_of_yesterday = local_datetime(self.yesterday, 23, 59, 59)


class CheckInTests(AttendanceTestCase):
    def check_in(self):
        return self.client.post(
            '/api/attendance/check-in/', {'member_id': self.member.id}, format='json',
        )

    def test_creates_open_attendance(self):
        response = self.check_in()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Attendance.objects.filter(member=self.member, check_out__isnull=True).exists()
        )

    def test_rejects_member_already_inside(self):
        open_attendance = Attendance.objects.create(member=self.member)

        response = self.check_in()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['attendance_id'], open_attendance.id)

    def test_closes_attendance_left_open_on_previous_day(self):
        stale = Attendance.objects.create(
            member=self.member, check_in=local_datetime(self.yesterday, 18),
        )

        response = self.check_in()

        self.assertEqual(response.status_code, 201)
        stale.refresh_from_db()
        self.assertEqual(stale.check_out, self.end_of_yesterday)

    def test_database_allows_one_open_attendance_per_member(self):
        Attendance.objects.create(member=self.member)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Attendance.objects.create(member=self.member)


class CheckOutTests(AttendanceTestCase):
    def test_closes_open_attendance(self):
        attendance = Attendance.objects.create(member=self.member)

        response = self.client.post(f'/api/attendance/{attendance.id}/check-out/')

        self.assertEqual(response.status_code, 200)
        attendance.refresh_from_db()
        self.assertIsNotNone(attendance.check_out)

    def test_attendance_from_previous_day_closes_at_end_of_that_day(self):
        attendance = Attendance.objects.create(
            member=self.member, check_in=local_datetime(self.yesterday, 18),
        )

        response = self.client.post(f'/api/attendance/{attendance.id}/check-out/')

        self.assertEqual(response.status_code, 200)
        attendance.refresh_from_db()
        self.assertEqual(attendance.check_out, self.end_of_yesterday)


class AttendanceListTests(AttendanceTestCase):
    def test_invalid_member_filter_returns_400(self):
        response = self.client.get('/api/attendance/', {'member': 'abc'})

        self.assertEqual(response.status_code, 400)

    def test_invalid_date_filter_returns_400(self):
        response = self.client.get('/api/attendance/', {'date': '2026-13-40'})

        self.assertEqual(response.status_code, 400)

    def test_date_filter_uses_local_day(self):
        day = date(2026, 1, 10)
        evening = Attendance.objects.create(
            member=self.member,
            check_in=local_datetime(day, 20),
            check_out=local_datetime(day, 21),
        )

        response = self.client.get('/api/attendance/', {'date': day.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [evening.id])


class ScanQrTests(AttendanceTestCase):
    def scan(self, code):
        return self.client.post('/api/attendance/scan/', {'code': code}, format='json')

    def test_member_scan_toggles_check_in_and_check_out(self):
        first = self.scan(self.member.qr_code)
        second = self.scan(self.member.qr_code)

        self.assertEqual(first.data['action'], 'check-in')
        self.assertEqual(second.data['action'], 'check-out')

    def test_member_scan_with_attendance_left_open_yesterday_checks_in(self):
        stale = Attendance.objects.create(
            member=self.member, check_in=local_datetime(self.yesterday, 18),
        )

        response = self.scan(self.member.qr_code)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['action'], 'check-in')
        stale.refresh_from_db()
        self.assertEqual(stale.check_out, self.end_of_yesterday)

    def test_coach_scan_with_attendance_left_open_yesterday_checks_in(self):
        stale = CoachAttendance.objects.create(
            coach=self.coach, check_in=local_datetime(self.yesterday, 18),
        )

        response = self.scan(self.coach.qr_code)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['action'], 'check-in')
        stale.refresh_from_db()
        self.assertEqual(stale.check_out, self.end_of_yesterday)


class CoachAttendanceTests(AttendanceTestCase):
    def test_check_in_closes_attendance_left_open_on_previous_day(self):
        stale = CoachAttendance.objects.create(
            coach=self.coach, check_in=local_datetime(self.yesterday, 18),
        )

        response = self.client.post(f'/api/coaches/{self.coach.id}/check-in/')

        self.assertEqual(response.status_code, 201)
        stale.refresh_from_db()
        self.assertEqual(stale.check_out, self.end_of_yesterday)

    def test_database_allows_one_open_attendance_per_coach(self):
        CoachAttendance.objects.create(coach=self.coach)

        with self.assertRaises(IntegrityError), transaction.atomic():
            CoachAttendance.objects.create(coach=self.coach)
