from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaches', '0003_close_duplicate_open_coach_attendances'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='coachattendance',
            constraint=models.UniqueConstraint(
                condition=models.Q(('check_out__isnull', True)),
                fields=('coach',),
                name='unique_open_attendance_per_coach',
            ),
        ),
    ]
