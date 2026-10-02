import random
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from members.models import Member


fake = Faker()


class Command(BaseCommand):
    """
    Seeder for members with random data using Faker.

    Usage:
        python manage.py seed_members
        python manage.py seed_members --count=50
        python manage.py seed_members --count=100 --flush
    """

    help = "Populates the database with random gym members using Faker"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of members to create (default: 100)",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing members before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]

        if options["flush"]:
            self.stdout.write(self.style.WARNING("[!] Deleting existing members..."))
            Member.all_objects.all().delete()
            self.stdout.write(self.style.SUCCESS("    Done.\n"))

        self.stdout.write(self.style.MIGRATE_HEADING(f"[*] Seeding {count} random members..."))
        self.stdout.write("-" * 50)

        statuses = [choice[0] for choice in Member.Status.choices]
        genders = [choice[0] for choice in Member.Gender.choices]

        created_count = 0
        skipped_count = 0

        for _ in range(count):
            gender = random.choice(genders)

            # Generate a name based on gender for realism
            if gender == Member.Gender.MALE:
                first_name = fake.first_name_male()
            elif gender == Member.Gender.FEMALE:
                first_name = fake.first_name_female()
            else:
                first_name = fake.first_name()

            last_name = fake.last_name()
            email = fake.unique.email()

            member, created = Member.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": fake.numerify("555-####"),
                    "date_of_birth": fake.date_of_birth(minimum_age=16, maximum_age=70),
                    "gender": gender,
                    "status": random.choice(statuses),
                },
            )

            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(f"[OK] {created_count} members created."))
        if skipped_count:
            self.stdout.write(self.style.WARNING(f"[--] {skipped_count} skipped (already existed)."))
        self.stdout.write(self.style.SUCCESS("\nSeeder completed!\n"))
