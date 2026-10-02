import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from memberships.models import Membership
from payments.models import Payment
from users.models import User

class Command(BaseCommand):
    help = "Genera pagos para las membresías existentes"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("[*] Generando pagos..."))
        
        memberships = list(Membership.objects.all())
        methods = [choice[0] for choice in Payment.Method.choices]
        admin_user = User.objects.filter(role=User.Role.ADMIN).first()

        if not memberships or not admin_user:
            self.stdout.write(self.style.ERROR("Faltan membresías o admin. Corre seed_memberships primero."))
            return

        created_count = 0
        for membership in memberships:
            # Check if payment already exists
            if not Payment.objects.filter(membership=membership).exists():
                # Randomize payment date around the start date of membership
                days_offset = random.randint(0, 2)
                payment_date = membership.start_date + timedelta(days=days_offset)
                # Convert to datetime by adding a random time
                payment_datetime = timezone.datetime.combine(payment_date, timezone.datetime.min.time())
                payment_datetime = timezone.make_aware(payment_datetime) + timedelta(hours=random.randint(8, 20))
                
                # Make payment
                payment = Payment(
                    membership=membership,
                    amount=membership.plan.price, # Full price
                    payment_date=payment_datetime,
                    method=random.choice(methods),
                    received_by=admin_user
                )
                payment.save()
                created_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"\n[OK] {created_count} pagos registrados.\n"))
