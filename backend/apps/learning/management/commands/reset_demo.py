from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command


class Command(BaseCommand):
    help = "Restore the deterministic fictional Pathloom demo dataset."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Confirm the local demo reset.")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("reset_demo is disabled when DJANGO_DEBUG is false.")
        if not options["confirm"]:
            raise CommandError("Pass --confirm to restore the demo database.")
        call_command("seed_demo", reset=True)
        self.stdout.write(self.style.SUCCESS("Demo data restored."))
