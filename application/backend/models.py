from django.db import models


class Role(models.Model):
    role_id = models.AutoField(primary_key=True, db_column='role_id')
    role_name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = 'role'

    def __str__(self):
        return self.role_name


class User(models.Model):
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    sfsu_email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, db_column='role_id', related_name='users')
    password_hash = models.CharField(max_length=256)
    account_status = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.sfsu_email


class Category(models.Model):
    category_id = models.AutoField(primary_key=True, db_column='category_id')
    category_name = models.CharField(max_length=128, unique=True)
    category_description = models.TextField(blank=True)

    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.category_name


class Listing(models.Model):
    listing_id = models.AutoField(primary_key=True, db_column='listing_id')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    listing_type = models.CharField(max_length=64)
    condition = models.CharField(max_length=64)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, db_column='category_id', related_name='listings')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, db_column='seller_id', related_name='listings')
    status = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'listing'

    def __str__(self):
        return self.title
