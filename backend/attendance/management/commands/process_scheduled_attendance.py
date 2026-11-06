from django.core.management.base import BaseCommand
from attendance.views import process_ended_sessions


class Command(BaseCommand):
    help = "Finalize ended SCOTT attendance sessions and create automatic absence records."

    def handle(self, *args, **options):
        process_ended_sessions()
        self.stdout.write(self.style.SUCCESS("Scheduled attendance processing completed."))
