"""
Django management command to expire trials that have passed their end date.
Run this as a cron job (e.g., daily).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.utils import expire_trials


class Command(BaseCommand):
    help = 'Expire trials that have passed their end date'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting trial expiration process...'))
        
        expired_count = expire_trials()
        
        if expired_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully expired {expired_count} trial(s)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No trials to expire')
            )
