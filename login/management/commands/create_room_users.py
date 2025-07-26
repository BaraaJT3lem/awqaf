from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from screen.models import ScreenSettings

class Command(BaseCommand):
    help = "Create/update room users with password '12345678' and no admin rights."

    def handle(self, *args, **kwargs):
        settings = ScreenSettings.get_settings()
        if not settings:
            self.stdout.write(self.style.ERROR("ScreenSettings not found."))
            return

        room_count = settings.room_count
        password = '12345678'

        for i in range(1, room_count + 1):
            username = f'room{i}'
            user, created = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.is_staff = False  # NO admin access
            user.is_superuser = False
            user.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated user: {username}"))
