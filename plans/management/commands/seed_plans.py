from django.core.management.base import BaseCommand
from django.db import transaction
from plans.models import Plan

class Command(BaseCommand):
    help = "Populates the database with initial gym plans"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("[*] Running Plans Seeder..."))
        self.stdout.write("-" * 50)

        plans_data = [
            {"name": "Mensual Básico", "price": "29.99", "duration_days": 30, "description": "Acceso a máquinas y pesas libres."},
            {"name": "Trimestral Pro", "price": "79.99", "duration_days": 90, "description": "Acceso total y clases grupales."},
            {"name": "Anual Premium", "price": "299.99", "duration_days": 365, "description": "Acceso total, clases grupales y 1 evaluación mensual gratis."},
        ]

        for data in plans_data:
            plan, created = Plan.objects.get_or_create(
                name=data["name"],
                defaults={
                    "price": data["price"],
                    "duration_days": data["duration_days"],
                    "description": data["description"],
                }
            )
            
            if created:
                status = self.style.SUCCESS("[OK] CREADO   ")
            else:
                status = self.style.WARNING("[--] YA EXISTE")
                
            self.stdout.write(f"  {status} | {plan.name:<18} | ${plan.price}")

        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS("\nSeeder de Planes completado!\n"))
