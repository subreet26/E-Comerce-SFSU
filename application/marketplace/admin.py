from django.contrib import admin
from django.utils import timezone

from .models import ApprovalStatus, Category, Listing, Message, PickupInformation, Product, Role, Service, User


@admin.action(description="Approve selected listings")
def approve_selected_listings(modeladmin, request, queryset):
    queryset.update(
        approval_status=ApprovalStatus.APPROVED,
        approved_by=request.user,
        approved_at=timezone.now(),
        rejection_reason="",
    )


@admin.action(description="Reject selected listings")
def reject_selected_listings(modeladmin, request, queryset):
    queryset.update(
        approval_status=ApprovalStatus.REJECTED,
        approved_by=request.user,
        approved_at=timezone.now(),
    )


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
    list_display = (
        'listing_id', 'title', 'price', 'listing_type', 'intent',
        'approval_status', 'category', 'condition', 'created_at',
    )
    list_filter = ('listing_type', 'condition', 'intent', 'approval_status', 'category')
    search_fields = ('title', 'description')
    actions = [approve_selected_listings, reject_selected_listings]


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
