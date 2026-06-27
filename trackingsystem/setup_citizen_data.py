#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trackingsystem.settings')
django.setup()

from django.contrib.auth.models import User
from landsystem.models import Citizen, OfficerProfile

# Create citizen users
citizens_data = [
    {'username': 'citizen1', 'password': 'password123', 'first_name': 'John', 'last_name': 'Mwita', 'phone': '0712345678', 'email': 'john@example.com'},
    {'username': 'citizen2', 'password': 'password123', 'first_name': 'Mary', 'last_name': 'Kimani', 'phone': '0723456789', 'email': 'mary@example.com'},
]

for citizen_data in citizens_data:
    username = citizen_data['username']
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            password=citizen_data['password'],
            first_name=citizen_data['first_name'],
            last_name=citizen_data['last_name'],
            email=citizen_data['email']
        )
        Citizen.objects.create(user=user, phone=citizen_data['phone'])
        print(f"Created citizen: {username}")
    else:
        print(f"Citizen already exists: {username}")

# Create/Update officer profiles
officers_data = [
    {'username': 'officer1', 'region': 'mbeya', 'phone': '0745123456'},
    {'username': 'officer2', 'region': 'dodoma', 'phone': '0745123457'},
    {'username': 'officer3', 'region': 'arusha', 'phone': '0745123458'},
]

for officer_data in officers_data:
    username = officer_data['username']
    user = User.objects.filter(username=username).first()
    if user:
        profile, created = OfficerProfile.objects.get_or_create(
            user=user,
            defaults={'region': officer_data['region'], 'phone': officer_data['phone']}
        )
        if created:
            print(f"Created officer profile: {username}")
        else:
            print(f"Officer profile exists: {username}")

print("\nTest data setup complete!")
