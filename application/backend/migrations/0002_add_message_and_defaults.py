# Generated manually for M3 backend updates

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        # Add default values to account_status and status fields
        migrations.AlterField(
            model_name='user',
            name='account_status',
            field=models.CharField(default='active', max_length=32),
        ),
        migrations.AlterField(
            model_name='listing',
            name='status',
            field=models.CharField(default='active', max_length=64),
        ),
        # Create the Message table
        migrations.CreateModel(
            name='Message',
            fields=[
                ('message_id', models.AutoField(db_column='message_id', primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(db_column='sender_id', on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='backend.user')),
                ('receiver', models.ForeignKey(db_column='receiver_id', on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='backend.user')),
                ('listing', models.ForeignKey(blank=True, db_column='listing_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='backend.listing')),
            ],
            options={
                'db_table': 'message',
                'ordering': ['created_at'],
            },
        ),
    ]
