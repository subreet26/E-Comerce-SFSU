from datetime import time

import django.db.models.deletion
from django.db import migrations, models


def seed_marketplace_data(apps, schema_editor):
    Role = apps.get_model('backend', 'Role')
    User = apps.get_model('backend', 'User')
    Category = apps.get_model('backend', 'Category')
    Listing = apps.get_model('backend', 'Listing')
    Product = apps.get_model('backend', 'Product')
    Service = apps.get_model('backend', 'Service')
    PickupInformation = apps.get_model('backend', 'PickupInformation')

    role, _ = Role.objects.get_or_create(role_name='Marketplace Seller')
    seller, _ = User.objects.get_or_create(
        sfsu_email='seed.marketplace@sfsu.edu',
        defaults={
            'first_name': 'Marketplace',
            'last_name': 'Seed',
            'role': role,
            'password_hash': 'seed-password-hash',
            'account_status': 'active',
        },
    )
    if seller.role_id != role.role_id:
        seller.role = role
        seller.save(update_fields=['role'])

    category_notes = {
        'Textbooks': 'Books, study guides, and classroom materials.',
        'Electronics': 'Phones, accessories, laptops, and tech gear.',
        'Furniture': 'Dorm and apartment furniture for students.',
        'Clothing': 'Apparel and accessories for campus life.',
        'Services': 'Campus-friendly services offered by students.',
        'Other': 'Anything that does not fit the main categories.',
    }

    categories = {}
    for category_name, description in category_notes.items():
        category, _ = Category.objects.update_or_create(
            category_name=category_name,
            defaults={'category_description': description},
        )
        categories[category_name] = category

    sample_items = [
        {
            'model': Product,
            'title': 'Desk Lamp',
            'description': 'Compact desk lamp with adjustable brightness.',
            'thumbnail_url': 'images/marketplace/placeholder-listing.svg',
            'price': '15.00',
            'listing_type': 'product',
            'status': 'for_sale',
            'condition': 'Good',
            'category': categories['Furniture'],
            'pickup_information': {
                'contact_method': 'Email',
                'pickup_time': time(17, 30),
                'visibility': 'buyers_only',
            },
        },
        {
            'model': Product,
            'title': 'Bike Lock',
            'description': 'Heavy-duty U-lock for commuting around campus.',
            'thumbnail_url': 'images/marketplace/placeholder-listing.svg',
            'price': '10.00',
            'listing_type': 'product',
            'status': 'wanted',
            'condition': 'New',
            'category': categories['Other'],
            'pickup_information': {
                'contact_method': 'Text',
                'pickup_time': time(18, 0),
                'visibility': 'public',
            },
        },
        {
            'model': Service,
            'title': 'Graphic Design Help',
            'description': 'Poster, flyer, and social media design support.',
            'thumbnail_url': 'images/marketplace/placeholder-listing.svg',
            'price': '25.00',
            'listing_type': 'service',
            'status': 'for_sale',
            'condition': 'New',
            'category': categories['Services'],
        },
        {
            'model': Product,
            'title': 'Headphones',
            'description': 'Over-ear headphones with wired and Bluetooth support.',
            'thumbnail_url': 'images/marketplace/placeholder-listing.svg',
            'price': '40.00',
            'listing_type': 'product',
            'status': 'for_sale',
            'condition': 'Like New',
            'category': categories['Electronics'],
            'pickup_information': {
                'contact_method': 'Email',
                'pickup_time': time(15, 0),
                'visibility': 'public',
            },
        },
    ]

    for item_data in sample_items:
        model = item_data.pop('model')
        pickup_information_data = item_data.pop('pickup_information', None)
        lookup = {
            'title': item_data['title'],
            'listing_type': item_data['listing_type'],
            'category': item_data['category'],
        }
        defaults = dict(item_data)
        defaults['seller'] = seller

        item, _ = model.objects.update_or_create(defaults=defaults, **lookup)

        if pickup_information_data is not None:
            pickup_information, _ = PickupInformation.objects.update_or_create(
                contact_method=pickup_information_data['contact_method'],
                pickup_time=pickup_information_data['pickup_time'],
                defaults={'visibility': pickup_information_data['visibility']},
            )
            item.pickup_information = pickup_information
            item.save(update_fields=['pickup_information'])


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PickupInformation',
            fields=[
                ('pickup_information_id', models.AutoField(primary_key=True, serialize=False)),
                ('contact_method', models.CharField(max_length=255)),
                ('pickup_time', models.TimeField(blank=True, null=True)),
                ('visibility', models.CharField(choices=[('public', 'Public'), ('buyers_only', 'Buyers Only'), ('private', 'Private')], default='public', max_length=20)),
            ],
            options={
                'db_table': 'pickup_information',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('item_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='backend.listing')),
                ('pickup_information', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product', to='backend.pickupinformation')),
            ],
            bases=('backend.listing',),
            options={
                'db_table': 'product',
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
            ],
            bases=('backend.listing',),
            options={
                'db_table': 'service',
            },
        ),
        migrations.RunPython(seed_marketplace_data, migrations.RunPython.noop),
    ]
