from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AdminAuditLog, SiteSetting

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions & Role', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'updated_at')}),
    )
    readonly_fields = ('date_joined', 'updated_at', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser'),
        }),
    )

@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'actor__email')
    readonly_fields = ('actor', 'action', 'ip_address', 'details', 'created_at')

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'updated_at')
    search_fields = ('key', 'description')

from .models import Consultant

@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'agency_name', 'city', 'total_leads', 'is_active', 'created_at')
    list_filter = ('is_active', 'city', 'created_at')
    search_fields = ('referral_code', 'user__email', 'user__first_name', 'user__last_name', 'agency_name')
    readonly_fields = ('referral_code', 'created_at', 'updated_at')

