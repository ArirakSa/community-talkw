from django.apps import AppConfig

class TalkwConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "talkw"

    def ready(self):
        import talkw.signals  # <-- เพิ่มบรรทัดนี้
