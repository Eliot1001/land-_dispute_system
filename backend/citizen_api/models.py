import random

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class PasswordResetCode(models.Model):
    """A short-lived numeric code emailed to a citizen so they can prove
    ownership of their account before setting a new password."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'citizen_password_reset_codes'

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=15)

    @staticmethod
    def generate_code():
        return f'{random.randint(0, 999999):06d}'
