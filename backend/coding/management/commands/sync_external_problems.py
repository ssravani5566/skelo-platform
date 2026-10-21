from django.core.management.base import BaseCommand, CommandError

from coding.external import PLATFORM_CHOICES
from coding.external_sync import sync_platform


LIVE_PLATFORMS = ["LEETCODE", "HACKERRANK", "CODECHEF", "CODEFORCES"]


class Command(BaseCommand):
    help = (
        "Sync real public coding-question metadata into SCOTT and retain links "
        "to the original platform. Use --platform ALL to sync every live catalog."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--platform",
            choices=["ALL"] + [x[0] for x in PLATFORM_CHOICES],
            required=True,
        )
        parser.add_argument("--limit", type=int, default=5000)

    def handle(self, *args, **options):
        platform = options["platform"]
        limit = max(1, min(options["limit"], 5000))

        if platform == "ALL":
            synced = {}
            errors = {}
            for target in LIVE_PLATFORMS:
                self.stdout.write(f"Syncing {target}...")
                try:
                    synced[target] = sync_platform(target, limit)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  {target}: synced {synced[target]} questions."
                        )
                    )
                except Exception as exc:
                    errors[target] = str(exc)
                    self.stderr.write(self.style.WARNING(f"  {target}: {exc}"))

            if not synced:
                raise CommandError(
                    "No external platform could be synced. "
                    + "; ".join(f"{k}: {v}" for k, v in errors.items())
                )

            self.stdout.write(
                self.style.SUCCESS(
                    "Finished external sync. "
                    + ", ".join(f"{k}={v}" for k, v in synced.items())
                )
            )
            if errors:
                self.stdout.write(
                    self.style.WARNING(
                        "Some platforms failed: "
                        + "; ".join(f"{k}: {v}" for k, v in errors.items())
                    )
                )
            return

        try:
            count = sync_platform(platform, limit)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(f"Synced {count} real {platform} questions.")
        )
