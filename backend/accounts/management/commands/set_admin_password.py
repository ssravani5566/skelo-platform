import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Set the password for the existing SKelo Admin account using Django password hashing."

    def add_arguments(self, parser):
        parser.add_argument("--password", dest="password", default=None, help="New password. Prefer INITIAL_ADMIN_PASSWORD in the backend .env file.")

    def handle(self, *args, **options):
        password = options.get("password") or os.getenv("INITIAL_ADMIN_PASSWORD")
        if not password:
            raise CommandError("Set INITIAL_ADMIN_PASSWORD in backend/.env or pass --password.")
        User = get_user_model()
        user = User.objects.filter(username__iexact="Admin", role="ADMIN").first()
        if user is None:
            user = User.objects.filter(role="ADMIN", is_superuser=True).order_by("id").first()
        if user is None:
            raise CommandError("No Admin user found. Run migrations first, then retry.")
        user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=["password", "is_active", "is_staff", "is_superuser"])
        self.stdout.write(self.style.SUCCESS(f"Updated password for Admin account: {user.username}"))
