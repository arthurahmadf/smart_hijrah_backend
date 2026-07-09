from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'


    def ready(self):
        # Panggil warmup saat server start (hanya jika embedding diperlukan)
        # try:
        #     from main.utils_embedding.embedder import warmup
        #     warmup()
        # except Exception as e:
        #     print(f"[EMBEDDER] ⚠️ Warmup failed: {e}")
        pass