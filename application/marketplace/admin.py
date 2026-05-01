from django.contrib import admin

from .models import Category, Listing, Message, PickupInformation, Product, Role, Service, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'sfsu_email', 'first_name', 'last_name', 'role', 'account_status')
    search_fields = ('sfsu_email', 'first_name', 'last_name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'category_name', 'category_description')
    search_fields = ('category_name',)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('listing_id', 'title', 'price', 'listing_type', 'intent', 'category', 'condition', 'created_at')
    list_filter = ('listing_type', 'condition', 'intent', 'category')
    search_fields = ('title', 'description')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'sender', 'receiver', 'listing', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('content',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('listing_id', 'title', 'price', 'category')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('listing_id', 'title', 'price', 'category')


@admin.register(PickupInformation)
class PickupInformationAdmin(admin.ModelAdmin):
    list_display = ('pickup_information_id', 'contact_method', 'pickup_time', 'visibility')
