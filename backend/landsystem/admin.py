from django.contrib import admin
from .models import Case, Citizen, OfficerProfile, CaseDocument, CaseFeedback

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'phone', 'region', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at']


@admin.register(OfficerProfile)
class OfficerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'region', 'phone', 'created_at']
    list_filter = ['level', 'region', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']


class CaseFeedbackInline(admin.StackedInline):
    model = CaseFeedback
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'citizen_name', 'region', 'current_level', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'current_level', 'region', 'created_at']
    search_fields = ['title', 'citizen_name', 'location', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CaseFeedbackInline]
    fieldsets = (
        ('Case Information', {
            'fields': ('title', 'description', 'status', 'current_level', 'level_updated_at', 'citizen')
        }),
        ('Citizen Information', {
            'fields': ('citizen_name', 'citizen_phone', 'citizen_email')
        }),
        ('Location', {
            'fields': ('location', 'ward', 'region', 'latitude', 'longitude')
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


@admin.register(CaseFeedback)
class CaseFeedbackAdmin(admin.ModelAdmin):
    list_display = ['case', 'rating', 'created_at', 'updated_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['case__title', 'case__citizen_name', 'comment']
    readonly_fields = ['created_at', 'updated_at']

