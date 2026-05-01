from django.contrib.auth.models import User as AuthUser
from django.db import models

from django.contrib.auth.hashers import make_password, check_password


class UserProfile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE, related_name='profile')
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    year = models.CharField(max_length=64, blank=True)
    major = models.CharField(max_length=128, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'

    @property
    def avatar(self):
        if self.avatar_url:
            return type('Avatar', (), {'url': self.avatar_url})()
        return None

    def __str__(self):
        return f"{self.user.username} profile"


def _get_auth_user_profile(auth_user):
    try:
        return auth_user.__dict__['_profile']
    except KeyError:
        try:
            profile = UserProfile.objects.get(user=auth_user)
        except Exception:
            profile = UserProfile(user=auth_user)
        auth_user.__dict__['_profile'] = profile
        return profile

AuthUser.profile = property(_get_auth_user_profile)


class MarketplaceUserProfile:
    def __init__(self, user):
        self.user = user

    @property
    def avatar(self):
        return None

    @property
    def is_verified(self):
        return False

    @property
    def year(self):
        return None

    @property
    def major(self):
        return None

    @property
    def bio(self):
        return ''

    def __str__(self):
        return f"{self.user.sfsu_email} profile"


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
    account_status = models.CharField(max_length=32, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.sfsu_email

    @property
    def username(self):
        return self.sfsu_email.split('@')[0]

    @property
    def email(self):
        return self.sfsu_email

    def get_full_name(self):
        full_name = ' '.join([name for name in [self.first_name, self.last_name] if name])
        return full_name.strip() or self.username

    @property
    def is_authenticated(self):
        return True

    @property
    def profile(self):
        return MarketplaceUserProfile(self)

    def set_password(self, raw_password):
        """Hash and store the password using Django's built-in PBKDF2 hasher."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Verify a raw password against the stored hash."""
        return check_password(raw_password, self.password_hash)


class Category(models.Model):
    category_id = models.AutoField(primary_key=True, db_column='category_id')
    category_name = models.CharField(max_length=128, unique=True)
    category_description = models.TextField(blank=True)

    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.category_name


class ListingType(models.TextChoices):
    PRODUCT = 'product', 'Product'
    SERVICE = 'service', 'Service'


class ListingIntent(models.TextChoices):
    FOR_SALE = 'for_sale', 'For Sale'
    WANTED = 'wanted', 'Wanted'


class PickupInformationVisibility(models.TextChoices):
    PUBLIC = 'public', 'Public'
    BUYERS_ONLY = 'buyers_only', 'Buyers Only'
    PRIVATE = 'private', 'Private'


class Listing(models.Model):
    listing_id = models.AutoField(primary_key=True, db_column='listing_id')
    description = models.TextField(blank=True)
    main_picture_url = models.URLField(max_length=500, blank=True, null=True, db_column='thumbnail_url')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    listing_type = models.CharField(max_length=32, choices=ListingType.choices, db_column='listing_type')
    intent = models.CharField(max_length=32, choices=ListingIntent.choices, db_column='status')
    condition = models.CharField(max_length=64, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, db_column='category_id', related_name='listings')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, db_column='seller_id', related_name='listings', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=200)
    condition = models.CharField(max_length=64)

    class Meta:
        db_table = 'listing'
        managed = False
        ordering = ['-created_at', '-listing_id']

    def __str__(self):
        return self.title
    


class Message(models.Model):
    message_id = models.AutoField(primary_key=True, db_column='message_id')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, db_column='sender_id', related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, db_column='receiver_id', related_name='received_messages')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, db_column='listing_id', related_name='messages', null=True, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message'
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"


class PickupInformation(models.Model):
    pickup_information_id = models.AutoField(primary_key=True)
    contact_method = models.CharField(max_length=255)
    pickup_time = models.TimeField(blank=True, null=True)
    visibility = models.CharField(
        max_length=20,
        choices=PickupInformationVisibility.choices,
        default=PickupInformationVisibility.PUBLIC,
    )

    class Meta:
        db_table = 'pickup_information'

    def __str__(self):
        return self.contact_method


class Product(Listing):
    pickup_information = models.OneToOneField(
        PickupInformation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product',
    )

    class Meta:
        db_table = 'product'


class Service(Listing):
    class Meta:
        db_table = 'service'
