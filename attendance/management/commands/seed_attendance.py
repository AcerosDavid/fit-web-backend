import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from attendance.models import Attendance
from members.models import Member
from users.models import User

class Command(BaseCommand):
    help = "Genera registros de asistencia aleatorios de los últimos 7 días"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("[*] Generando asistencias..."))
        
        members = list(Member.objects.filter(status=Member.Status.ACTIVE, memberships__isnull=False).distinct())
        admin_user = User.objects.filter(role=User.Role.ADMIN).first()

        if not members or not admin_user:
            self.stdout.write(self.style.ERROR("Faltan miembros con membresía o admin. Corre seed_memberships primero."))
            return

        created_count = 0
        now = timezone.now()
        
        for i in range(7): # For the last 7 days
            day_date = now - timedelta(days=i)
            
            # Select 10-20 random members to visit that day
            daily_visitors = random.sample(members, min(len(members), random.randint(10, 20)))
            
            for member in daily_visitors:
                # Random entry time between 6 AM and 8 PM
                entry_hour = random.randint(6, 20)
                entry_minute = random.randint(0, 59)
                
                check_in = day_date.replace(hour=entry_hour, minute=entry_minute, second=0, microsecond=0)
                
                # Training duration: 45 to 120 minutes
                duration = timedelta(minutes=random.randint(45, 120))
                check_out = check_in + duration
                
                # If the checkout time is in the future (they are training right now)
                if check_out > now:
                    check_out = None
                
                Attendance.objects.create(
                    member=member,
                    check_in=check_in,
                    check_out=check_out,
                    registered_by=admin_user
                )
                created_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"\n[OK] {created_count} asistencias registradas.\n"))
