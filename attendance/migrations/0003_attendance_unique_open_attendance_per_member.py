from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_close_duplicate_open_attendances'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(
                condition=models.Q(('check_out__isnull', True)),
                fields=('member',),
                name='unique_open_attendance_per_member',
            ),
        ),
    ]
