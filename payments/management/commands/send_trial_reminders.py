"""
Django management command to send trial expiration reminder emails.
Run this as a cron job (e.g., daily).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.utils import get_trials_expiring_soon
from payments.emails import send_trial_expiring_email


class Command(BaseCommand):
    help = 'Send reminder emails for trials expiring soon (3 days before)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Number of days before expiration to send reminder (default: 3)'
        )

    def handle(self, *args, **options):
        days_before = options['days']
        
        self.stdout.write(
            self.style.WARNING(f'Checking for trials expiring in {days_before} days...')
        )
        
        trials = get_trials_expiring_soon(days_before=days_before)
        sent_count = 0
        
        for trial in trials:
            try:
                send_trial_expiring_email(trial.user, trial)
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Sent reminder to {trial.user.email} for {trial.strategy_name}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send email to {trial.user.email}: {str(e)}')
                )
        
        if sent_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent {sent_count} reminder email(s)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No reminders to send')
            )
