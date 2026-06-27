from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


class Citizen(models.Model):
    """Model for citizen users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='citizen_profile')
    phone = models.CharField(max_length=20)
    region = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'citizens'
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class OfficerProfile(models.Model):
    """Model for case officer profiles"""
    REGION_CHOICES = [
        ('arusha', 'Arusha Region'),
        ('dar_es_salaam', 'Dar es Salaam'),
        ('dodoma', 'Dodoma Region'),
        ('iringa', 'Iringa Region'),
        ('kagera', 'Kagera Region'),
        ('mbeya', 'Mbeya Region'),
        ('mwanza', 'Mwanza Region'),
        ('tanga', 'Tanga Region'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='officer_profile')
    region = models.CharField(max_length=50, choices=REGION_CHOICES)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'officers'
    
    def __str__(self):
        return f"Officer {self.user.username} - {self.get_region_display()}"


class Case(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
    ]
    
    REGION_CHOICES = [
        ('arusha', 'Arusha Region'),
        ('dar_es_salaam', 'Dar es Salaam'),
        ('dodoma', 'Dodoma Region'),
        ('iringa', 'Iringa Region'),
        ('kagera', 'Kagera Region'),
        ('mbeya', 'Mbeya Region'),
        ('mwanza', 'Mwanza Region'),
        ('tanga', 'Tanga Region'),
    ]
    
    title = models.CharField(max_length=255)
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, null=True, blank=True, related_name='submitted_cases')
    citizen_name = models.CharField(max_length=255)
    citizen_phone = models.CharField(max_length=20)
    citizen_email = models.EmailField(blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default='dodoma')
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'cases'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class CaseDocument(models.Model):
    """Model for case evidence documents"""
    DOCUMENT_TYPES = [
        ('evidence', 'Evidence'),
        ('receipt', 'Receipt'),
        ('photo', 'Photo'),
        ('letter', 'Letter'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='evidence')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='case_documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    
    class Meta:
        db_table = 'case_documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - Case #{self.case.id}"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.file:
            name, ext = os.path.splitext(self.file.name)
            return ext.lstrip('.')
        return ''



