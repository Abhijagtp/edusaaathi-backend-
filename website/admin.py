from django.contrib import admin
from .models import Course, IndianCity, Lead, ContactMessage, FAQ

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'duration', 'fees', 'published', 'is_featured', 'created_at')
    list_filter = ('published', 'is_featured', 'category')
    search_fields = ('name', 'slug', 'short_description', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('published', 'is_featured')

@admin.register(IndianCity)
class IndianCityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'tier', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('tier', 'is_active', 'state')
    search_fields = ('name', 'state')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'mobile_number', 'course_interest', 'city', 'status', 'created_at')
    list_filter = ('status', 'city', 'created_at')
    search_fields = ('full_name', 'mobile_number', 'email', 'course_interest', 'other_course', 'city')
    readonly_fields = ('created_at', 'updated_at', 'ip_address')
    list_editable = ('status',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_active')
    list_editable = ('order', 'is_active')
