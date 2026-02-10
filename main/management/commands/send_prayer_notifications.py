from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from zoneinfo import ZoneInfo
from firebase_admin import messaging
from main.firebase import init_firebase

from main.models import (
    PrayerMonthDocument,
    UserPrayerPreference,
    PrayerNotificationLog,
)

init_firebase()


def parse_local_datetime(dt_str, tz_name):
    tz = ZoneInfo(tz_name)
    naive = datetime.fromisoformat(dt_str.replace("Z", ""))
    return naive.replace(tzinfo=tz)


class Command(BaseCommand):
    help = "Send prayer notifications based on user preferences"

    def send_notification(self, user, prayer_name, prayer_time,location):
        if not user.fcm_token:
            return

        message = messaging.Message(
            token=user.fcm_token,
            notification=messaging.Notification(
                title="Pengingat Waktu Shalat",
                body=f"Memasuki waktu {prayer_name.capitalize()} untuk {location}",
            ),
            data={
                "type": "prayer",
                "prayer": prayer_name,
                "time": prayer_time.isoformat(),
            },
            android=messaging.AndroidConfig(
                priority="high",
                ttl=timezone.timedelta(minutes=5),  # optional but recommended
                notification=messaging.AndroidNotification(
                    channel_id="high_importance_channel",
                    sound="default",
                    visibility="public",
                ),
            ),
        )
        response = messaging.send(message)
        self.stdout.write(f"FCM sent: {response}")

    def handle(self, *args, **options):
        utc_now = timezone.now()  # ✅ only once

        docs = PrayerMonthDocument.objects.all()

        for doc in docs:
            user = doc.user
            lokasi = doc.location
            try:
                prefs = UserPrayerPreference.objects.get(user=user)
            except UserPrayerPreference.DoesNotExist:
                continue

            local_now = utc_now.astimezone(
                ZoneInfo(doc.timezone)
            )

            today_str = local_now.date().isoformat()

            today = None
            for day in doc.payload.get("Jadwale", []):
                if today_str in day["date"]:
                    today = day
                    break

            if not today:
                continue

            for item in today.get("jadwal_ibadah", []):
                name = item["name"].lower()  # ✅ normalize

                if not hasattr(prefs, name):
                    continue

                if not getattr(prefs, name):
                    continue

                if PrayerNotificationLog.objects.filter(
                    user=user,
                    date=today_str,
                    prayer_name=name,
                ).exists():
                    continue

                prayer_time = parse_local_datetime(
                    item["time"],
                    doc.timezone
                )

                if local_now < prayer_time:
                    continue

                self.send_notification(user, name, prayer_time,lokasi)

                PrayerNotificationLog.objects.create(
                    user=user,
                    date=today_str,
                    prayer_name=name,
                )

        self.stdout.write("✔ Prayer notification run completed")
