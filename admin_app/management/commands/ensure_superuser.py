import os
from django.core.management.base import BaseCommand
from admin_app.models import User

class Command(BaseCommand):
    help = 'Ensures the EduSaathi admin superuser exists with the correct credentials and permissions'

    def handle(self, *args, **options):
        email = os.getenv('SUPERUSER_EMAIL', 'edusaathi@gmail.com').strip()
        password = os.getenv('SUPERUSER_PASSWORD', 'edusaathi9897@!').strip()
        first_name = os.getenv('SUPERUSER_FIRST_NAME', 'EduSaathi')
        last_name = os.getenv('SUPERUSER_LAST_NAME', 'Admin')

        self.stdout.write(f"Checking superuser: {email}...")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )

        # Update attributes to ensure administrative rights
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.role = 'ADMIN'
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser: {email}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser {email} already exists; updated credentials and administrative permissions."))
