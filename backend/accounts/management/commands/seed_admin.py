import os

from django.core.management.base import BaseCommand

from accounts.models import AdminUser


class Command(BaseCommand):
    help = "Seed the default admin account."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-reset-password",
            action="store_true",
            help="Do not reset the password when the admin user already exists.",
        )

    def handle(self, *args, **options):
        username = _env("ADMIN_USERNAME", "SEED_ADMIN_USERNAME", default="admin")
        email = _env("ADMIN_EMAIL", "SEED_ADMIN_EMAIL", default="admin@example.com")
        password = _env("ADMIN_PASSWORD", "SEED_ADMIN_PASSWORD", default="MoodFlow@123456")
        role = _env("ADMIN_ROLE", "SEED_ADMIN_ROLE", default=AdminUser.Role.SUPER_ADMIN)
        status = _env("ADMIN_STATUS", "SEED_ADMIN_STATUS", default=AdminUser.Status.ACTIVE)

        admin_user, created = AdminUser.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": role,
                "status": status,
            },
        )
        admin_user.email = email
        admin_user.role = role
        admin_user.status = status
        if created or not options["no_reset_password"]:
            admin_user.set_password(password)
        admin_user.save()

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Admin user {username!r} {action}."))


def _env(*names, default):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default
