from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_approved(apps, schema_editor):
    Listing = apps.get_model('marketplace', 'Listing')
    Listing.objects.all().update(approval_status='approved')


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0003_merge_0002_alter_user_role_0002_userprofile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='approval_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                db_index=True,
                default='pending',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='listing',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_listings',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='listing',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='listing',
            name='rejection_reason',
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(backfill_approved, migrations.RunPython.noop),
    ]
