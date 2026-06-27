from django.contrib import admin
from .models import Case, Citizen, OfficerProfile, CaseDocument

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'phone', 'region', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at']


@admin.register(OfficerProfile)
class OfficerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'region', 'phone', 'created_at']
    list_filter = ['region', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'citizen_name', 'region', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'region', 'created_at']
    search_fields = ['title', 'citizen_name', 'location', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Case Information', {
            'fields': ('title', 'description', 'status', 'citizen')
        }),
        ('Citizen Information', {
            'fields': ('citizen_name', 'citizen_phone', 'citizen_email')
        }),
        ('Location', {
            'fields': ('location', 'region', 'latitude', 'longitude')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'case', 'document_type', 'file_extension', 'uploaded_at', 'uploaded_by']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['title', 'case__title', 'case__citizen_name']
    readonly_fields = ['uploaded_at', 'file_extension']

