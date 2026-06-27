from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from landsystem.models import Case

class Command(BaseCommand):
    help = 'Populate database with test case data'

    def handle(self, *args, **options):
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin'))
        
        # Create test users
        users_data = [
            {'username': 'officer1', 'email': 'officer1@example.com', 'first_name': 'John', 'last_name': 'Smith'},
            {'username': 'officer2', 'email': 'officer2@example.com', 'first_name': 'Jane', 'last_name': 'Doe'},
            {'username': 'officer3', 'email': 'officer3@example.com', 'first_name': 'Robert', 'last_name': 'Johnson'},
        ]
        
        users = {}
        for user_data in users_data:
            username = user_data['username']
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=user_data['email'],
                    password='password123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                users[username] = user
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            else:
                users[username] = User.objects.get(username=username)
        
        # Create test cases
        cases_data = [
            {
                'title': 'Land Boundary Dispute - Mbeya Region',
                'citizen_name': 'John Mwita',
                'citizen_phone': '0712345678',
                'location': 'Mbeya',
                'latitude': -8.7731,
                'longitude': 33.4597,
                'description': 'Two families are disputing over land boundary marks. The property has been in the family for generations but recent surveys show conflicting boundaries.',
                'status': 'pending',
            },
            {
                'title': 'Farm Land Conflict - Mwanza',
                'citizen_name': 'Asha Komba',
                'citizen_phone': '0723456789',
                'location': 'Mwanza',
                'latitude': -2.5198,
                'longitude': 32.9022,
                'description': 'Dispute over agricultural land usage rights. One party claims customary rights while the other has official documentation.',
                'status': 'in_progress',
                'assigned_to': users.get('officer1'),
            },
            {
                'title': 'Inheritance Land Dispute - Arusha',
                'citizen_name': 'Peter John',
                'citizen_phone': '0734567890',
                'location': 'Arusha',
                'latitude': -3.3731,
                'longitude': 36.6753,
                'description': 'Multiple heirs claiming rights to inherited property. Missing official documentation for the estate.',
                'status': 'resolved',
                'assigned_to': users.get('officer2'),
                'notes': 'Case resolved through mediation. All parties agreed on property division.',
            },
            {
                'title': 'Boundary Encroachment - Dar es Salaam',
                'citizen_name': 'Mary Hassan',
                'citizen_phone': '0745678901',
                'location': 'Dar es Salaam',
                'latitude': -6.8000,
                'longitude': 39.2803,
                'description': 'Neighbor has allegedly encroached on property by constructing boundary wall beyond agreed limits.',
                'status': 'escalated',
                'assigned_to': users.get('officer3'),
                'notes': 'Case escalated due to neighbor non-compliance and threats.',
            },
            {
                'title': 'Land Lease Dispute - Dodoma',
                'citizen_name': 'Samuel Moshi',
                'citizen_phone': '0756789012',
                'location': 'Dodoma',
                'latitude': -6.1639,
                'longitude': 35.7465,
                'description': 'Landlord and tenant disagreement over lease terms and property condition assessment.',
                'status': 'in_progress',
                'assigned_to': users.get('officer1'),
            },
            {
                'title': 'Communal Land Rights - Kagera',
                'citizen_name': 'Grace Niwamanya',
                'citizen_phone': '0767890123',
                'location': 'Kagera',
                'latitude': -1.3521,
                'longitude': 31.8559,
                'description': 'Community members claiming rights to traditionally communal land being appropriated for private use.',
                'status': 'pending',
            },
            {
                'title': 'Document Fraud Case - Iringa',
                'citizen_name': 'David Mwakyusa',
                'citizen_phone': '0778901234',
                'location': 'Iringa',
                'latitude': -8.3704,
                'longitude': 35.6899,
                'description': 'Suspicion of forged land ownership documents in property transaction.',
                'status': 'escalated',
                'assigned_to': users.get('officer2'),
            },
            {
                'title': 'Urban Plot Conflict - Tanga',
                'citizen_name': 'Rebecca Kimaro',
                'citizen_phone': '0789012345',
                'location': 'Tanga',
                'latitude': -5.0269,
                'longitude': 39.2025,
                'description': 'Dispute over prime urban land with conflicting survey reports from different periods.',
                'status': 'resolved',
                'assigned_to': users.get('officer3'),
                'notes': 'Resolved through court mediation based on oldest valid survey.',
            },
        ]
        
        created_count = 0
        for case_data in cases_data:
            assigned_to = case_data.pop('assigned_to', None)
            notes = case_data.pop('notes', '')
            
            if not Case.objects.filter(title=case_data['title']).exists():
                case = Case.objects.create(**case_data, assigned_to=assigned_to, notes=notes)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created case: {case.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} test cases'))
