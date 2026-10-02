import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from memberships.models import Membership
from members.models import Member
from plans.models import Plan
from users.models import User

class Command(BaseCommand):
    help = "Asigna membresías aleatorias a los clientes"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("[*] Asignando membresías..."))
        
        members = list(Member.objects.filter(status=Member.Status.ACTIVE))
        plans = list(Plan.objects.filter(is_active=True))
        admin_user = User.objects.filter(role=User.Role.ADMIN).first()

        if not members or not plans or not admin_user:
            self.stdout.write(self.style.ERROR("Faltan datos base (miembros, planes o admin). Corre los seeders anteriores primero."))
            return

        created_count = 0
        for member in members:
            # Randomly decide if they have a membership right now (80% chance)
            if random.random() < 0.8:
                plan = random.choice(plans)
                
                # Assign start date anywhere from 30 days ago to today
                days_ago = random.randint(0, 30)
                start_date = timezone.now().date() - timedelta(days=days_ago)
                
                # Check if it doesn't already have one
                if not Membership.objects.filter(member=member).exists():
                    membership = Membership(
                        member=member,
                        plan=plan,
                        start_date=start_date,
                        created_by=admin_user
                    )
                    membership.save() # save() calculates end_date
                    created_count += 1
                    
        self.stdout.write(self.style.SUCCESS(f"\n[OK] {created_count} membresías creadas.\n"))
