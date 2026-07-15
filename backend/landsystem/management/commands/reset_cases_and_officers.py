from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from landsystem.models import Case, OfficerProfile


class Command(BaseCommand):
    help = (
        'Deletes every case (and its documents/feedback) and every officer '
        'account except superusers. Citizen accounts are left untouched.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='Confirm the deletion (required).')

    def handle(self, *args, **options):
        if not options['yes']:
            raise CommandError(
                'This permanently deletes every case and every officer account except '
                'superusers. Re-run with --yes to confirm.'
            )

        case_count = Case.objects.count()
        officer_profiles = list(OfficerProfile.objects.select_related('user'))
        officer_users = [op.user for op in officer_profiles if not op.user.is_superuser]
        kept_superusers = len(officer_profiles) - len(officer_users)

        with transaction.atomic():
            Case.objects.all().delete()
            for user in officer_users:
                user.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Deleted {case_count} case(s) and {len(officer_users)} officer account(s). '
            f'Kept {kept_superusers} superuser account(s) and all citizen accounts.'
        ))
