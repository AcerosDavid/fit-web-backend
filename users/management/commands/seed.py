from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User


class Command(BaseCommand):
    """
    Seeder para la app users.
    Equivalente a: php artisan db:seed --class=UsersSeeder en Laravel.

    Uso:
        python manage.py seed
        python manage.py seed --flush   (borra los usuarios antes de insertar)
    """

    help = "Puebla la base de datos con usuarios de prueba (Administrador y Recepcionista)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Elimina todos los usuarios existentes antes de insertar los nuevos.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write(self.style.WARNING("[!] Eliminando usuarios existentes..."))
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("    Usuarios eliminados correctamente.\n"))

        self.stdout.write(self.style.MIGRATE_HEADING("[*] Ejecutando Seeder de Usuarios..."))
        self.stdout.write("-" * 50)

        users_data = [
            {
                "username": "admin",
                "email": "admin@fitgym.com",
                "password": "admin1234",
                "first_name": "Carlos",
                "last_name": "Garcia",
                "role": User.Role.ADMIN,
                "is_staff": True,
            },
            {
                "username": "recepcionista",
                "email": "recepcion@fitgym.com",
                "password": "recep1234",
                "first_name": "Maria",
                "last_name": "Lopez",
                "role": User.Role.RECEPTIONIST,
                "is_staff": False,
            },
        ]

        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": data["role"],
                    "is_staff": data["is_staff"],
                },
            )

            if created:
                user.set_password(data["password"])
                user.save()
                status = self.style.SUCCESS("[OK] CREADO   ")
            else:
                status = self.style.WARNING("[--] YA EXISTE")

            self.stdout.write(
                f"  {status} | {data['role']:<15} | {data['username']:<20} | pass: {data['password']}"
            )

        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS("\nSeeder ejecutado con exito!\n"))
